import json

from contractguard.cli import _write_report
from contractguard.models import AnalysisResult, ContractType, Issue, Protection, Severity


def _sample_result() -> AnalysisResult:
    return AnalysisResult(
        contract_type=ContractType.LEASE,
        summary="A one-sided lease.",
        parties=["Tenant", "Landlord"],
        key_terms=["12 months"],
        red_flags=[
            Issue(
                title="Non-refundable deposit",
                severity=Severity.RED,
                clause="Section 3",
                quote="deposit is non-refundable",
                explanation="Deposits are usually refundable.",
                suggestion="Remove the non-refundable language.",
            )
        ],
        warnings=[],
        good_clauses=[
            Protection(
                title="Written notice",
                clause="Section 1",
                explanation="Both sides need written notice.",
            )
        ],
        missing_protections=["Grace period"],
        fairness_score=40,
        fairness_grade="C",
    )


def test_write_report_uses_json_when_json_flag_is_set(tmp_path):
    output = tmp_path / "report.json"

    _write_report(_sample_result(), str(output), json_output=True)

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["contract_type"] == "lease"
    assert data["red_flags"][0]["title"] == "Non-refundable deposit"


def test_write_report_defaults_to_markdown(tmp_path):
    output = tmp_path / "report.md"

    _write_report(_sample_result(), str(output))

    content = output.read_text(encoding="utf-8")
    assert "# ContractGuard Analysis Report" in content
    assert "Non-refundable deposit" in content


def test_write_report_creates_parent_directories(tmp_path):
    output = tmp_path / "reports" / "lease" / "report.md"

    _write_report(_sample_result(), str(output))

    assert output.exists()


def test_write_report_pdf_suffix_writes_a_real_pdf(tmp_path):
    output = tmp_path / "report.pdf"

    _write_report(_sample_result(), str(output))

    assert output.read_bytes()[:5] == b"%PDF-"
    import pdfplumber

    with pdfplumber.open(str(output)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    assert "ContractGuard Analysis Report" in text
    assert "Non-refundable deposit" in text
