"""Tests for the Gradio web UI's statute-check panel."""

from __future__ import annotations

import pytest

pytest.importorskip("gradio")

from contractguard.models import AnalysisResult, ContractType
from contractguard.web import _analyze, create_app

CA_LEASE = """\
CALIFORNIA RESIDENTIAL LEASE AGREEMENT
This Lease shall be governed by the laws of the State of California.
Monthly rent shall be $3,200.00, due on the first day of each month.
Tenant shall pay a security deposit of $6,400.00 before move-in.
Landlord shall return the security deposit within 21 days of move-out, with an itemized statement.
Landlord may enter the Property with at least 24 hours' written notice to Tenant.
"""

CN_EMPLOYMENT = """\
劳动合同书
甲方：某科技有限公司。乙方：张三。
本合同期限三年，自 2025 年 1 月 1 日起至 2027 年 12 月 31 日止。
试用期八个月，试用期工资为约定工资的 80%。
"""


class _Upload:
    """Stand-in for the Gradio upload object; only .name is read."""

    def __init__(self, path):
        self.name = str(path)


def _llm_result(contract_type: ContractType) -> AnalysisResult:
    return AnalysisResult(
        contract_type=contract_type,
        summary="s",
        fairness_score=50,
        fairness_grade="C",
    )


def _scan(tmp_path, monkeypatch, text, contract_type, lang):
    contract = tmp_path / "contract.txt"
    contract.write_text(text, encoding="utf-8")
    monkeypatch.setattr(
        "contractguard.web.analyze_contract", lambda **_: _llm_result(contract_type)
    )
    return _analyze(_Upload(contract), "test-model", "", lang)


def test_ca_lease_panel_flags_deposit_cap_violation(tmp_path, monkeypatch):
    _, _, _, _, statute, report = _scan(
        tmp_path, monkeypatch, CA_LEASE, ContractType.LEASE, "en"
    )
    assert "## Statute Checks" in statute
    assert "Security deposit cap" in statute
    assert "VIOLATION" in statute
    assert "1950.5" in statute
    assert "$6,400.00" in statute

    # the downloadable HTML report carries the same checks
    assert report.endswith(".html")
    with open(report, encoding="utf-8") as f:
        html = f.read()
    assert "Statute Checks" in html
    assert "Security deposit cap" in html


def test_cn_employment_panel_flags_probation_violation(tmp_path, monkeypatch):
    _, _, _, _, statute, _ = _scan(
        tmp_path, monkeypatch, CN_EMPLOYMENT, ContractType.EMPLOYMENT, "zh"
    )
    assert "## 法条核查" in statute
    assert "违规" in statute
    assert "试用期上限" in statute
    assert "劳动合同法" in statute


def test_app_builds_offline():
    assert create_app() is not None
