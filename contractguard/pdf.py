"""PDF report rendering with reportlab — the dependency-free fallback.

weasyprint renders the full HTML report with pixel fidelity but needs system
libraries (cairo/pango), which are not installable everywhere. This module
renders the same report with reportlab's platypus, a pure-wheel dependency,
so PDF export works on any host. weasyprint stays the preferred path when
installed; this renderer is the everywhere-works fallback.
"""

from __future__ import annotations

from contractguard.disclaimers import DISCLAIMER, SCOPE_NOTE
from contractguard.models import AnalysisResult, Issue, StatuteCheck
from contractguard.references import reference_for

_GRADE_HEX = {
    "A+": "#16a34a",
    "A": "#16a34a",
    "B+": "#4d7c0f",
    "B": "#ca8a04",
    "C+": "#ca8a04",
    "C": "#ea580c",
    "D": "#dc2626",
    "F": "#b91c1c",
}
_CARD_BORDER = {"red": "#dc2626", "yellow": "#ca8a04", "green": "#16a34a", "gray": "#94a3b8"}
_STATUTE_KIND = {"violation": "red", "ok": "green", "unknown": "gray"}
_STATUTE_LABEL = {
    "en": {"violation": "VIOLATION", "ok": "OK", "unknown": "UNKNOWN"},
    "zh": {"violation": "违规", "ok": "符合", "unknown": "无法判断"},
}


def _styles(lang: str = "en"):
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle

    font_name = "Helvetica"
    quote_font = "Helvetica-Oblique"
    if lang == "zh":
        # 内置 CID 字体，无字体文件也能在任何阅读器渲染中文
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont

        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        font_name = quote_font = "STSong-Light"

    return {
        "title": ParagraphStyle("title", fontName=font_name, fontSize=20, leading=26, spaceAfter=6),
        "meta": ParagraphStyle("meta", fontName=font_name, fontSize=10, textColor="#475569", spaceAfter=2),
        "h2": ParagraphStyle("h2", fontName=font_name, fontSize=15, leading=19, spaceBefore=18, spaceAfter=8),
        "h3": ParagraphStyle("h3", fontName=font_name, fontSize=12, leading=16, spaceAfter=4),
        "clause": ParagraphStyle("clause", fontName=font_name, fontSize=9, textColor="#64748b", spaceAfter=4),
        "body": ParagraphStyle("body", fontName=font_name, fontSize=10, leading=14, spaceAfter=4),
        "quote": ParagraphStyle(
            "quote",
            fontName=quote_font,
            fontSize=10,
            leading=14,
            textColor="#334155",
            leftIndent=8,
            spaceBefore=4,
            spaceAfter=4,
        ),
        "label": ParagraphStyle("label", fontName=font_name, fontSize=10, leading=14, spaceAfter=4),
        "bullet": ParagraphStyle("bullet", fontName=font_name, fontSize=10, leading=14, leftIndent=14, spaceAfter=3),
        "footer": ParagraphStyle(
            "footer",
            fontName=font_name,
            fontSize=8.5,
            leading=12,
            textColor="#94a3b8",
            alignment=TA_CENTER,
            spaceBefore=6,
        ),
    }


def _card(flowables, kind, styles):
    """A bordered card: left color bar, light background, kept on one page."""
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import KeepTogether, Table, TableStyle

    border = colors.HexColor(_CARD_BORDER[kind])
    table = Table([[flowables]], colWidths=[170 * mm])
    table.setStyle(
        TableStyle(
            [
                ("LINEBEFORE", (0, 0), (0, -1), 2.5, border),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return KeepTogether([table])


def _spacer(points: float = 8):
    from reportlab.platypus import Spacer

    return Spacer(1, points)


def _esc(text: object) -> str:
    """Escape user/contract text for reportlab's mini-HTML."""
    import html as _html

    return _html.escape(str(text), quote=True)


def render_pdf_report(result: AnalysisResult, lang: str, path: str) -> str:
    """Render the analysis report to ``path`` with reportlab. Returns path."""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph, SimpleDocTemplate

    styles = _styles(lang)
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=18 * 2.835,
        rightMargin=18 * 2.835,
        topMargin=20 * 2.835,
        bottomMargin=20 * 2.835,
        title=f"ContractGuard Report — {result.contract_type.value}",
    )

    def P(text: str, style: str = "body"):
        return Paragraph(text, styles[style])

    story = []
    story.append(P("ContractGuard Analysis Report", "title"))
    contract_type = result.contract_type.value.replace("_", " ").title()
    story.append(P(f"Contract type: {_esc(contract_type)}", "meta"))
    story.append(P(f"Parties: {_esc(', '.join(result.parties) or '—')}", "meta"))
    grade_color = _GRADE_HEX.get(result.fairness_grade, "#475569")
    score = max(0, min(100, result.fairness_score))
    story.append(_spacer(6))
    story.append(
        P(
            f'<font backColor="{grade_color}" color="white"><b> '
            f"{_esc(result.fairness_grade)} · {score}/100 </b></font>",
            "body",
        )
    )

    story.append(P("Summary", "h2"))
    story.append(P(_esc(result.summary)))

    if result.key_terms:
        story.append(P("Key Terms", "h2"))
        for term in result.key_terms:
            story.append(P(f"• {_esc(term)}", "bullet"))

    def add_cards(items, kind: str, heading: str, rows_fn) -> None:
        if not items:
            return
        story.append(P(heading, "h2"))
        for item in items:
            cells = [Paragraph(t, styles[s]) for t, s in rows_fn(item)]
            story.append(_card(cells, kind, styles))
            story.append(_spacer(6))

    add_cards(result.red_flags, "red", "Red Flags", lambda i: _issue_rows(i, lang))
    add_cards(result.warnings, "yellow", "Warnings", lambda i: _issue_rows(i, lang))
    if result.statute_checks:
        story.append(P("Statute Checks", "h2"))
        for check in result.statute_checks:
            cells = [Paragraph(t, styles[s]) for t, s in _statute_rows(check, lang)]
            story.append(_card(cells, _STATUTE_KIND[check.status.value], styles))
            story.append(_spacer(6))
    add_cards(
        result.good_clauses,
        "green",
        "Good Clauses",
        lambda p: [(f"<b>{_esc(p.title)}</b>", "h3"), (_esc(p.clause), "clause"), (_esc(p.explanation), "body")],
    )
    if result.missing_protections:
        story.append(P("Missing Protections", "h2"))
        for m in result.missing_protections:
            story.append(P(f"• {_esc(m)}", "bullet"))

    lang_key = "zh" if lang == "zh" else "en"
    story.append(_spacer(16))
    story.append(P(_esc(DISCLAIMER[lang_key]), "footer"))
    story.append(P(_esc(SCOPE_NOTE[lang_key]), "footer"))
    story.append(P("Generated by ContractGuard — never sign a bad contract again.", "footer"))

    doc.build(story)
    return path


def _issue_rows(issue: Issue, lang: str) -> list[tuple[str, str]]:
    redline_label = "建议改写：" if lang == "zh" else "Suggested rewrite:"
    rows = [
        (f"<b>{_esc(issue.title)}</b>", "h3"),
        (_esc(issue.clause), "clause"),
        (f"<i>{_esc(issue.quote)}</i>", "quote"),
        (_esc(issue.explanation), "body"),
        (f"<b>Suggestion:</b> {_esc(issue.suggestion)}", "body"),
    ]
    if issue.redline:
        rows.append((f'<font backColor="#f0fdf4"><b>{redline_label}</b> {_esc(issue.redline)}</font>', "body"))
    return rows


def _statute_rows(check: StatuteCheck, lang: str) -> list[tuple[str, str]]:
    status = check.status.value
    label = _STATUTE_LABEL["zh" if lang == "zh" else "en"][status]
    ref = reference_for(check.rule_id)
    basis = _esc(check.basis)
    if ref:
        basis = f'<link href="{_esc(ref)}" color="#2563eb"><u>{basis}</u></link>'
    rows = [
        (f"<b>{_esc(check.title)}</b>", "h3"),
        (f"{basis} · {label}", "clause"),
    ]
    if check.quote and status == "violation":
        rows.append((f"<i>{_esc(check.quote)}</i>", "quote"))
    rows.append((_esc(check.detail), "body"))
    return rows
