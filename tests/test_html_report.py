"""Tests for the self-contained HTML report export."""

from contractguard.html import generate_html_report
from contractguard.models import AnalysisResult, ContractType, Issue, Protection, Severity


def _result(**overrides) -> AnalysisResult:
    base = AnalysisResult(
        contract_type=ContractType.LEASE,
        summary="A lease with one nasty clause.",
        parties=["Tenant Co", "Landlord LLC"],
        key_terms=["12 months", "$2,000/month"],
        red_flags=[
            Issue(
                title="Non-refundable deposit",
                clause="Section 3",
                quote="The security deposit is <b>non-refundable</b> under all circumstances.",
                explanation="Tenants normally get deposits back.",
                suggestion="Make it refundable minus documented damage.",
                severity=Severity.RED,
            )
        ],
        warnings=[],
        good_clauses=[
            Protection(
                title="Quiet enjoyment",
                clause="Section 7",
                explanation="Standard protection.",
            )
        ],
        missing_protections=["Early termination right"],
        fairness_score=42,
        fairness_grade="D",
    )
    return base.model_copy(update=overrides)


def test_report_contains_header_score_and_sections():
    html_out = generate_html_report(_result())
    assert "ContractGuard Analysis Report" in html_out
    assert "D · 42/100" in html_out
    assert 'width:42%' in html_out
    assert "Tenant Co, Landlord LLC" in html_out
    assert "<h2>Red Flags</h2>" in html_out
    assert "<h2>Good Clauses</h2>" in html_out
    assert "Early termination right" in html_out


def test_report_is_self_contained():
    html_out = generate_html_report(_result())
    assert "<style>" in html_out
    assert "http://" not in html_out and "https://" not in html_out
    assert "<script" not in html_out.lower()


def test_contract_text_is_html_escaped():
    html_out = generate_html_report(_result())
    # the malicious-looking quote must be escaped, not rendered as markup
    assert "<b>non-refundable</b>" not in html_out
    assert "&lt;b&gt;non-refundable&lt;/b&gt;" in html_out


def test_empty_sections_are_omitted():
    html_out = generate_html_report(
        _result(red_flags=[], warnings=[], good_clauses=[], missing_protections=[], key_terms=[])
    )
    assert "<h2>Red Flags</h2>" not in html_out
    assert "<h2>Warnings</h2>" not in html_out
    assert "<h2>Good Clauses</h2>" not in html_out
    assert "<h2>Missing Protections</h2>" not in html_out
    assert "<h2>Key Terms</h2>" not in html_out
