"""Tests for jurisdiction detection and the California lease rules."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from contractguard.checklist import detect_jurisdiction, run_checklist
from contractguard.cli import batch, scan
from contractguard.models import AnalysisResult, ContractType, StatuteCheck, StatuteStatus

SAMPLE_LEASE = Path(__file__).parent.parent / "examples" / "sample_lease.txt"


def _checks(text: str, contract_type: str = "lease", jurisdiction: str = "us-ca"):
    return {c.rule_id: c for c in run_checklist(text, contract_type, "en", jurisdiction=jurisdiction)}


# ---------------------------------------------------------------------------
# Jurisdiction detection
# ---------------------------------------------------------------------------


def test_detect_chinese_contract_is_cn():
    assert detect_jurisdiction("劳动合同期限三年，试用期六个月。") == "cn"


def test_detect_california_governing_law_is_us_ca():
    text = "This Lease shall be governed by the laws of the State of California."
    assert detect_jurisdiction(text) == "us-ca"


def test_detect_california_premises_address_is_us_ca():
    text = "RESIDENTIAL LEASE. Premises: 9 Elm Street, Oakland, CA 94610. Rent is due monthly."
    assert detect_jurisdiction(text) == "us-ca"


# ---------------------------------------------------------------------------
# Security deposit cap (Civil Code §1950.5, as amended by AB 12)
# ---------------------------------------------------------------------------


def test_deposit_over_one_month_is_violation():
    text = "Monthly rent shall be $3,200.00. Tenant shall pay a security deposit of $6,400.00."
    check = _checks(text)["us_ca_security_deposit_cap"]
    assert check.status == StatuteStatus.VIOLATION
    assert "1950.5" in check.basis
    assert "$6,400.00" in check.detail and "$3,200.00" in check.detail


def test_deposit_at_one_month_is_ok():
    text = "Monthly rent shall be $3,200.00. Tenant shall pay a security deposit of $3,200.00."
    check = _checks(text)["us_ca_security_deposit_cap"]
    assert check.status == StatuteStatus.OK


def test_deposit_stated_in_months_of_rent_is_violation():
    text = "Monthly rent shall be $2,000.00. Tenant shall pay a security deposit equal to two months' rent."
    check = _checks(text)["us_ca_security_deposit_cap"]
    assert check.status == StatuteStatus.VIOLATION
    assert "one month" in check.detail


def test_deposit_cap_unknown_without_amounts():
    text = "Tenant shall pay a security deposit before move-in."
    check = _checks(text)["us_ca_security_deposit_cap"]
    assert check.status == StatuteStatus.UNKNOWN


# ---------------------------------------------------------------------------
# Deposit refundability (Civil Code §1950.5)
# ---------------------------------------------------------------------------


def test_nonrefundable_deposit_is_violation():
    text = "The security deposit is non-refundable and shall be retained by Landlord upon termination."
    check = _checks(text)["us_ca_deposit_refundability"]
    assert check.status == StatuteStatus.VIOLATION
    assert "non-refundable" in check.quote


def test_deposit_without_nonrefundable_language_is_ok():
    text = "Tenant shall pay a security deposit of $3,000.00 before move-in."
    check = _checks(text)["us_ca_deposit_refundability"]
    assert check.status == StatuteStatus.OK


# ---------------------------------------------------------------------------
# Landlord entry notice (Civil Code §1954)
# ---------------------------------------------------------------------------


def test_entry_without_notice_is_violation():
    text = "Landlord shall have the right to enter the Property at any time, with or without notice."
    check = _checks(text)["us_ca_entry_notice"]
    assert check.status == StatuteStatus.VIOLATION
    assert "1954" in check.basis


def test_entry_24_hour_notice_is_ok():
    text = "Landlord may enter the Property with at least 24 hours' written notice to Tenant."
    check = _checks(text)["us_ca_entry_notice"]
    assert check.status == StatuteStatus.OK


def test_entry_shorter_notice_is_violation():
    text = "Landlord may enter the Property upon 12 hours' notice to Tenant."
    check = _checks(text)["us_ca_entry_notice"]
    assert check.status == StatuteStatus.VIOLATION
    assert "24" in check.detail


def test_entry_reasonable_notice_without_hours_is_unknown():
    text = "Landlord may enter the Property with reasonable advance notice."
    check = _checks(text)["us_ca_entry_notice"]
    assert check.status == StatuteStatus.UNKNOWN


# ---------------------------------------------------------------------------
# Deposit return deadline (Civil Code §1950.5(g))
# ---------------------------------------------------------------------------


def test_deposit_return_over_21_days_is_violation():
    text = "Landlord shall refund the security deposit within 45 days after termination."
    check = _checks(text)["us_ca_deposit_return_deadline"]
    assert check.status == StatuteStatus.VIOLATION
    assert "21" in check.detail


def test_deposit_return_within_21_days_is_ok():
    text = "Landlord shall return the security deposit within 21 days of move-out, with an itemized statement."
    check = _checks(text)["us_ca_deposit_return_deadline"]
    assert check.status == StatuteStatus.OK


# ---------------------------------------------------------------------------
# Auto detection end to end
# ---------------------------------------------------------------------------


def test_demo_lease_auto_flags_readme_scenarios():
    # the README's demo lease: non-refundable two-month deposit, entry
    # "with or without notice", and no deposit-return deadline at all
    checks = _checks(SAMPLE_LEASE.read_text(encoding="utf-8"), jurisdiction="auto")
    assert checks["us_ca_security_deposit_cap"].status == StatuteStatus.VIOLATION
    assert checks["us_ca_deposit_refundability"].status == StatuteStatus.VIOLATION
    assert checks["us_ca_entry_notice"].status == StatuteStatus.VIOLATION
    assert checks["us_ca_deposit_return_deadline"].status == StatuteStatus.UNKNOWN
    assert not any(rid.startswith("cn_") for rid in checks)


def test_auto_unknown_jurisdiction_reports_honestly():
    text = (
        "This Non-Disclosure Agreement is entered into by the parties. "
        "Each party shall protect confidential information."
    )
    checks = run_checklist(text, "unknown", "en")
    by_id = {c.rule_id: c for c in checks}
    assert by_id["jurisdiction_detection"].status == StatuteStatus.UNKNOWN
    assert not any(rid.startswith("us_ca_") for rid in by_id)


def test_explicit_cn_skips_ca_rules():
    text = "This Lease is governed by the laws of the State of California. Monthly rent shall be $3,200.00."
    checks = _checks(text, jurisdiction="cn")
    assert "cn_lease_term_cap" in checks
    assert not any(rid.startswith("us_ca_") for rid in checks)


# ---------------------------------------------------------------------------
# CLI plumbing
# ---------------------------------------------------------------------------


def _llm_result() -> AnalysisResult:
    return AnalysisResult(
        contract_type=ContractType.LEASE,
        summary="s",
        fairness_score=50,
        fairness_grade="C",
    )


def test_cli_scan_and_batch_forward_jurisdiction(tmp_path, monkeypatch):
    contract = tmp_path / "c.txt"
    contract.write_text("a contract", encoding="utf-8")
    monkeypatch.setattr("contractguard.parser.extract_text", lambda *a, **k: "the contract text")
    monkeypatch.setattr("contractguard.analyzer.analyze_contract", lambda **_: _llm_result())

    seen: list[str] = []

    def spy(text, contract_type, lang, jurisdiction="auto"):
        seen.append(jurisdiction)
        return [
            StatuteCheck(
                rule_id="us_ca_entry_notice",
                title="Landlord entry notice",
                basis="California Civil Code §1954",
                status=StatuteStatus.UNKNOWN,
                detail="No landlord entry clause found.",
            )
        ]

    monkeypatch.setattr("contractguard.checklist.run_checklist", spy)

    result = CliRunner().invoke(scan, [str(contract), "--json", "--jurisdiction", "us-ca"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["statute_checks"][0]["rule_id"] == "us_ca_entry_notice"

    out_dir = tmp_path / "reports"
    result = CliRunner().invoke(batch, [str(contract), "--jurisdiction", "us-ca", "-o", str(out_dir)])
    assert result.exit_code == 0
    assert seen == ["us-ca", "us-ca"]
    assert "## Statute Checks" in (out_dir / "c.md").read_text(encoding="utf-8")
