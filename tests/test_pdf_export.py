"""PDF export sits next to the HTML report, with a reportlab fallback so it
works on hosts without weasyprint's system libraries."""

from contractguard.html import write_pdf_report
from contractguard.models import (
    AnalysisResult,
    ContractType,
    Issue,
    Severity,
    StatuteCheck,
    StatuteStatus,
)


def test_pdf_export_returns_none_without_weasyprint(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def no_weasyprint(name, *args, **kwargs):
        if name in ("weasyprint", "contractguard.pdf"):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_weasyprint)
    assert write_pdf_report(None, "en") is None


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
                quote="The security deposit is non-refundable under all circumstances.",
                explanation="Tenants normally get deposits back.",
                suggestion="Make it refundable minus documented damage.",
                severity=Severity.RED,
            )
        ],
        warnings=[],
        good_clauses=[],
        missing_protections=["Early termination right"],
        fairness_score=42,
        fairness_grade="D",
        statute_checks=[
            StatuteCheck(
                rule_id="us_ca_security_deposit_cap",
                title="Security deposit cap",
                basis="California Civil Code §1950.5",
                status=StatuteStatus.VIOLATION,
                detail="Deposit exceeds one month's rent.",
                quote="The security deposit is non-refundable under all circumstances.",
            )
        ],
    )
    return base.model_copy(update=overrides)


def test_pdf_export_reportlab_fallback_produces_a_real_pdf(tmp_path, monkeypatch):
    """Without weasyprint, the reportlab fallback still writes a real PDF
    carrying the score, the statute basis, and the disclaimer."""
    import builtins

    real_import = builtins.__import__

    def no_weasyprint(name, *args, **kwargs):
        if name == "weasyprint":
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_weasyprint)

    out = tmp_path / "report.pdf"
    path = write_pdf_report(_result(), "en", str(out))
    assert path == str(out)
    assert out.read_bytes()[:5] == b"%PDF-"

    import pdfplumber

    with pdfplumber.open(str(out)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    assert "ContractGuard Analysis Report" in text
    assert "D · 42/100" in text
    assert "Non-refundable deposit" in text
    assert "California Civil Code §1950.5" in text
    assert "VIOLATION" in text
    assert "not legal advice" in text.lower() or "不构成法律意见" in text


def test_pdf_export_reportlab_fallback_chinese(tmp_path, monkeypatch):
    """The zh report carries the Chinese status labels and disclaimer."""
    import builtins

    real_import = builtins.__import__

    def no_weasyprint(name, *args, **kwargs):
        if name == "weasyprint":
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_weasyprint)

    out = tmp_path / "report-zh.pdf"
    write_pdf_report(_result(), "zh", str(out))
    import pdfplumber

    with pdfplumber.open(str(out)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    assert "违规" in text
