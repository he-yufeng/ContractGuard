"""Disclaimer and scope boundaries: every user-facing surface states them.

Roadmap #4 item 3: "not legal advice" plus the audited scope (CA residential
leases, PRC labor contracts) must be on the home page and on report footers,
in both languages.
"""

from contractguard.disclaimers import DISCLAIMER, SCOPE_NOTE
from contractguard.html import generate_html_report
from contractguard.models import AnalysisResult, ContractType
from contractguard.report import generate_markdown_report
from contractguard.disclaimers import HOME_MD_EN, HOME_MD_ZH


def _result() -> AnalysisResult:
    return AnalysisResult(
        contract_type=ContractType.LEASE,
        summary="A lease.",
        parties=["Tenant Co", "Landlord LLC"],
        key_terms=[],
        red_flags=[],
        warnings=[],
        good_clauses=[],
        missing_protections=[],
        fairness_score=90,
        fairness_grade="A",
    )


def test_disclaimer_and_scope_exist_in_both_languages():
    assert "not legal advice" in DISCLAIMER["en"]
    assert "不构成法律意见" in DISCLAIMER["zh"]
    assert "California" in SCOPE_NOTE["en"] and "PRC" in SCOPE_NOTE["en"]
    assert "加州" in SCOPE_NOTE["zh"] and "中国" in SCOPE_NOTE["zh"]


def test_html_report_footer_carries_disclaimer_and_scope():
    en = generate_html_report(_result(), lang="en")
    zh = generate_html_report(_result(), lang="zh")

    assert DISCLAIMER["en"] in en
    assert SCOPE_NOTE["en"] in en
    assert DISCLAIMER["zh"] in zh
    assert SCOPE_NOTE["zh"] in zh


def test_markdown_report_footer_carries_disclaimer_and_scope():
    en = generate_markdown_report(_result(), lang="en")
    zh = generate_markdown_report(_result(), lang="zh")

    assert DISCLAIMER["en"] in en
    assert SCOPE_NOTE["en"] in en
    assert DISCLAIMER["zh"] in zh
    assert SCOPE_NOTE["zh"] in zh


def test_home_page_states_disclaimer_and_scope():
    assert "not legal advice" in HOME_MD_EN
    assert "California" in HOME_MD_EN
    assert "不构成法律意见" in HOME_MD_ZH
    assert "加州" in HOME_MD_ZH
