"""Gradio web UI for ContractGuard."""

from __future__ import annotations

import os
import tempfile

import gradio as gr

from contractguard.analyzer import DEFAULT_MODEL, analyze_contract
from contractguard.disclaimers import HOME_MD_EN, HOME_MD_ZH
from contractguard.checklist import run_checklist
from contractguard.html import generate_html_report, write_pdf_report
from contractguard.models import StatuteCheck
from contractguard.parser import extract_text
from contractguard.references import reference_for

# Same palette as the score card: red / green / gray.
_STATUS_CHIPS = {
    "en": {"violation": ("#ef4444", "VIOLATION"), "ok": ("#22c55e", "OK"), "unknown": ("#6b7280", "UNKNOWN")},
    "zh": {"violation": ("#ef4444", "违规"), "ok": ("#22c55e", "符合"), "unknown": ("#6b7280", "无法判断")},
}


def _statute_md(checks: list[StatuteCheck], lang: str) -> str:
    if not checks:
        return ""
    chips = _STATUS_CHIPS["zh" if lang == "zh" else "en"]
    violations = sum(1 for c in checks if c.status.value == "violation")
    if lang == "zh":
        md = f"## 法条核查\n\n共 {len(checks)} 项核查，**{violations} 项违规**\n\n"
        basis_label = "依据"
    else:
        md = f"## Statute Checks\n\n**{violations} violation(s)** of {len(checks)} checks\n\n"
        basis_label = "Basis"
    for i, check in enumerate(checks, 1):
        color, label = chips[check.status.value]
        md += f"### {i}. {check.title}\n"
        md += f'<span style="color:{color}; font-weight:600;">{label}</span>  \n'
        ref = reference_for(check.rule_id)
        basis_md = f"[{check.basis}]({ref})" if ref else check.basis
        md += f"**{basis_label}:** {basis_md}  \n"
        if check.quote:
            md += f"> {check.quote}\n\n"
        md += f"{check.detail}\n\n---\n\n"
    return md


def _write_html_report(result, lang: str) -> str:
    fd, path = tempfile.mkstemp(prefix="contractguard-", suffix=".html")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(generate_html_report(result, lang))
    return path



def _analyze(file, model: str, api_key: str, lang: str = "en"):
    if file is None:
        return "Upload a file to get started.", "", "", "", "", None, None

    try:
        text = extract_text(file.name)
    except Exception as e:
        return f"**Error:** {e}", "", "", "", "", None, None

    kwargs = {"contract_text": text, "model": model or DEFAULT_MODEL, "lang": lang}
    if api_key and api_key.strip():
        kwargs["api_key"] = api_key.strip()

    try:
        result = analyze_contract(**kwargs)
    except Exception as e:
        return f"**Error:** {e}", "", "", "", "", None, None

    # Statute checks need no LLM; reuse the CLI engine with auto jurisdiction.
    result.statute_checks = run_checklist(text, result.contract_type.value, lang)
    statute_md = _statute_md(result.statute_checks, lang)
    report_path = _write_html_report(result, lang)

    # Score card
    grade_colors = {
        "A+": "#22c55e", "A": "#22c55e", "B+": "#84cc16", "B": "#eab308",
        "C+": "#f97316", "C": "#f97316", "D": "#ef4444", "F": "#dc2626",
    }
    color = grade_colors.get(result.fairness_grade, "#6b7280")
    score_html = f"""
    <div style="text-align:center; padding:24px;">
        <div style="font-size:64px; font-weight:800; color:{color}; line-height:1;">
            {result.fairness_grade}
        </div>
        <div style="font-size:20px; color:#888; margin-top:4px;">
            {result.fairness_score} / 100
        </div>
        <div style="margin-top:16px; display:flex; justify-content:center; gap:16px; flex-wrap:wrap;">
            <span style="color:#ef4444; font-weight:600;">{len(result.red_flags)} Red Flags</span>
            <span style="color:#f59e0b; font-weight:600;">{len(result.warnings)} Warnings</span>
            <span style="color:#22c55e; font-weight:600;">{len(result.good_clauses)} Protections</span>
            <span style="color:#6b7280; font-weight:600;">{len(result.missing_protections)} Missing</span>
        </div>
    </div>
    """

    # Summary
    summary_md = (
        f"**Type:** {result.contract_type.value.replace('_', ' ').title()}  \n"
        f"**Parties:** {', '.join(result.parties)}  \n\n"
        f"{result.summary}\n\n"
        f"**Key Terms:** {', '.join(result.key_terms[:5])}"
    )

    # Red flags & warnings
    issues_md = ""
    redline_label = "建议改写：" if lang == "zh" else "Suggested rewrite:"

    def _issue_md(rank: int, issue) -> str:
        block = (
            f"### {rank}. {issue.title}\n"
            f"**Clause:** {issue.clause}  \n"
            f"> {issue.quote}\n\n"
            f"{issue.explanation}  \n"
            f"**Suggestion:** {issue.suggestion}  \n"
        )
        if issue.redline:
            block += f"**{redline_label}** {issue.redline}  \n"
        return block + "\n---\n\n"

    if result.red_flags:
        issues_md += "## Red Flags\n\n"
        for i, f in enumerate(result.red_flags, 1):
            issues_md += _issue_md(i, f)
    if result.warnings:
        issues_md += "## Warnings\n\n"
        for i, w in enumerate(result.warnings, 1):
            issues_md += _issue_md(i, w)

    # Protections & missing
    protections_md = ""
    if result.good_clauses:
        protections_md += "## Protections Found\n\n"
        for p in result.good_clauses:
            protections_md += f"- **{p.title}** ({p.clause}) — {p.explanation}\n"
    if result.missing_protections:
        protections_md += "\n## Missing Protections\n\n"
        for m in result.missing_protections:
            protections_md += f"- {m}\n"

    pdf_path = write_pdf_report(result, lang)
    return score_html, summary_md, issues_md, protections_md, statute_md, report_path, pdf_path


def create_app() -> gr.Blocks:
    with gr.Blocks(title="ContractGuard") as app:
        gr.Markdown(HOME_MD_EN + "\n\n---\n\n" + HOME_MD_ZH)

        with gr.Row():
            with gr.Column(scale=1, min_width=280):
                file_input = gr.File(
                    label="Upload Contract",
                    file_types=[".pdf", ".docx", ".txt", ".md"],
                )
                model_input = gr.Textbox(
                    label="Model",
                    value=DEFAULT_MODEL,
                    placeholder="gpt-4o / anthropic/claude-sonnet-4",
                )
                api_key_input = gr.Textbox(
                    label="API Key (optional if set via env var)",
                    type="password",
                    placeholder="sk-...",
                )
                lang_input = gr.Dropdown(
                    label="Language",
                    choices=[("English", "en"), ("中文", "zh")],
                    value="en",
                )
                scan_btn = gr.Button("Scan Contract", variant="primary", size="lg")

            with gr.Column(scale=1, min_width=280):
                score_output = gr.HTML(label="Fairness Score")
                summary_output = gr.Markdown(label="Summary")

        with gr.Row():
            with gr.Column():
                issues_output = gr.Markdown(label="Issues Found")
            with gr.Column():
                protections_output = gr.Markdown(label="Protections")

        with gr.Row():
            with gr.Column():
                statute_output = gr.Markdown(label="Statute Checks")

        report_output = gr.File(label="Download HTML Report")
        pdf_output = gr.File(label="Download PDF Report (needs the pdf extra)")

        scan_btn.click(
            fn=_analyze,
            inputs=[file_input, model_input, api_key_input, lang_input],
            outputs=[score_output, summary_output, issues_output, protections_output, statute_output, report_output, pdf_output],
        )

    return app


def main():
    app = create_app()
    app.launch()


if __name__ == "__main__":
    main()
