"""Gradio web UI for ContractGuard."""

from __future__ import annotations

import gradio as gr

from contractguard.analyzer import DEFAULT_MODEL, analyze_contract
from contractguard.parser import extract_text


def _analyze(file, model: str, api_key: str, lang: str = "en"):
    if file is None:
        return "Upload a file to get started.", "", "", ""

    try:
        text = extract_text(file.name)
    except Exception as e:
        return f"**Error:** {e}", "", "", ""

    kwargs = {"contract_text": text, "model": model or DEFAULT_MODEL, "lang": lang}
    if api_key and api_key.strip():
        kwargs["api_key"] = api_key.strip()

    try:
        result = analyze_contract(**kwargs)
    except Exception as e:
        return f"**Error:** {e}", "", "", ""

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
    if result.red_flags:
        issues_md += "## Red Flags\n\n"
        for i, f in enumerate(result.red_flags, 1):
            issues_md += (
                f"### {i}. {f.title}\n"
                f"**Clause:** {f.clause}  \n"
                f"> {f.quote}\n\n"
                f"{f.explanation}  \n"
                f"**Suggestion:** {f.suggestion}\n\n---\n\n"
            )
    if result.warnings:
        issues_md += "## Warnings\n\n"
        for i, w in enumerate(result.warnings, 1):
            issues_md += (
                f"### {i}. {w.title}\n"
                f"**Clause:** {w.clause}  \n"
                f"> {w.quote}\n\n"
                f"{w.explanation}  \n"
                f"**Suggestion:** {w.suggestion}\n\n---\n\n"
            )

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

    return score_html, summary_md, issues_md, protections_md


def create_app() -> gr.Blocks:
    with gr.Blocks(title="ContractGuard") as app:
        gr.Markdown(
            "# ContractGuard\n\n"
            "Upload a contract and get an instant AI review with red flags, "
            "warnings, protections, and a fairness score.\n\n"
            "*Not legal advice. Use as a first-pass filter before consulting a lawyer.*"
        )

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

        scan_btn.click(
            fn=_analyze,
            inputs=[file_input, model_input, api_key_input, lang_input],
            outputs=[score_output, summary_output, issues_output, protections_output],
        )

    return app


def main():
    app = create_app()
    app.launch()


if __name__ == "__main__":
    main()
