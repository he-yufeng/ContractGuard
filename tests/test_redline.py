"""Tests for clause-level negotiation drafts (Issue.redline)."""

import json

from click.testing import CliRunner

from contractguard import report as report_mod
from contractguard.cli import scan
from contractguard.html import generate_html_report
from contractguard.models import AnalysisResult, ContractType, Issue, Severity
from contractguard.prompts import ANALYSIS_PROMPT, ANALYSIS_PROMPT_ZH
from contractguard.report import generate_markdown_report, print_report

REDLINE = (
    "The security deposit shall be refunded within 14 days of move-out, "
    "minus documented repair costs."
)
REDLINE_ZH = "押金应于退租后14日内退还，仅可扣除有凭证的维修费用。"


def _issue(**overrides) -> Issue:
    base = dict(
        title="Non-refundable deposit",
        severity=Severity.RED,
        clause="Section 3",
        quote="The security deposit is non-refundable.",
        explanation="Most jurisdictions require deposits to be refundable.",
        suggestion="Ask for the deposit to be refundable minus documented damage.",
    )
    base.update(overrides)
    return Issue(**base)


def _result(**issue_overrides) -> AnalysisResult:
    return AnalysisResult(
        contract_type=ContractType.LEASE,
        summary="A lease with one nasty clause.",
        parties=["Tenant Co", "Landlord LLC"],
        key_terms=["12 months"],
        red_flags=[_issue(**issue_overrides)],
        fairness_score=42,
        fairness_grade="D",
    )


def _render_terminal(result: AnalysisResult, lang: str = "en") -> str:
    with report_mod.console.capture() as cap:
        print_report(result, lang=lang)
    # Rich wraps at console width; collapse whitespace so wrapped text stays findable
    return " ".join(cap.get().split())


# Model behavior

def test_issue_redline_defaults_to_empty():
    assert _issue().redline == ""


def test_issue_accepts_redline():
    assert _issue(redline=REDLINE).redline == REDLINE


def test_llm_response_without_redline_still_validates():
    # responses from before this feature (or models that ignore the new key)
    data = {
        "contract_type": "lease",
        "summary": "s",
        "red_flags": [
            {
                "title": "t",
                "severity": "red",
                "clause": "c",
                "quote": "q",
                "explanation": "e",
                "suggestion": "s",
            }
        ],
        "fairness_score": 50,
        "fairness_grade": "C",
    }
    result = AnalysisResult(**data)
    assert result.red_flags[0].redline == ""


# Prompts

def test_prompts_ask_for_redline():
    assert '"redline"' in ANALYSIS_PROMPT
    assert '"redline"' in ANALYSIS_PROMPT_ZH


# Terminal report

def test_terminal_report_shows_redline_en():
    out = _render_terminal(_result(redline=REDLINE))
    assert "Suggested rewrite:" in out
    assert REDLINE in out


def test_terminal_report_shows_redline_zh():
    out = _render_terminal(_result(redline=REDLINE_ZH), lang="zh")
    assert "建议改写：" in out
    assert REDLINE_ZH in out


def test_terminal_report_omits_redline_when_empty():
    out = _render_terminal(_result())
    assert "Suggested rewrite:" not in out
    assert "建议改写：" not in out


# Markdown report

def test_markdown_report_shows_redline_en():
    md = generate_markdown_report(_result(redline=REDLINE))
    assert f"**Suggested rewrite:** {REDLINE}" in md


def test_markdown_report_shows_redline_zh():
    md = generate_markdown_report(_result(redline=REDLINE_ZH), lang="zh")
    assert f"**建议改写：** {REDLINE_ZH}" in md


def test_markdown_report_omits_redline_when_empty():
    md = generate_markdown_report(_result())
    assert "Suggested rewrite:" not in md


# HTML report

def test_html_report_shows_redline_block():
    html = generate_html_report(_result(redline=REDLINE))
    assert 'class="redline"' in html
    assert "Suggested rewrite:" in html
    assert REDLINE in html


def test_html_report_escapes_redline():
    html = generate_html_report(_result(redline="deposit <b>shall</b> be refundable"))
    assert "deposit <b>shall</b>" not in html
    assert "&lt;b&gt;shall&lt;/b&gt;" in html


def test_html_report_omits_redline_when_empty():
    html = generate_html_report(_result())
    assert 'class="redline"' not in html


# JSON output

def test_to_json_omits_empty_redline():
    payload = json.loads(_result().to_json())
    assert "redline" not in payload["red_flags"][0]


def test_to_json_includes_redline_when_present():
    payload = json.loads(_result(redline=REDLINE).to_json())
    assert payload["red_flags"][0]["redline"] == REDLINE


def test_to_json_keeps_unicode_readable():
    raw = _result(redline=REDLINE_ZH).to_json()
    assert REDLINE_ZH in raw


def test_scan_json_carries_redline(tmp_path, monkeypatch):
    contract = tmp_path / "c.txt"
    contract.write_text("a contract", encoding="utf-8")
    monkeypatch.setattr("contractguard.parser.extract_text", lambda *a, **k: "text")
    monkeypatch.setattr(
        "contractguard.analyzer.analyze_contract",
        lambda **_: _result(redline=REDLINE),
    )
    monkeypatch.setattr("contractguard.checklist.run_checklist", lambda *a, **k: [])

    result = CliRunner().invoke(scan, [str(contract), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["red_flags"][0]["redline"] == REDLINE


def test_scan_json_drops_empty_redline(tmp_path, monkeypatch):
    contract = tmp_path / "c.txt"
    contract.write_text("a contract", encoding="utf-8")
    monkeypatch.setattr("contractguard.parser.extract_text", lambda *a, **k: "text")
    monkeypatch.setattr(
        "contractguard.analyzer.analyze_contract",
        lambda **_: _result(),
    )
    monkeypatch.setattr("contractguard.checklist.run_checklist", lambda *a, **k: [])

    result = CliRunner().invoke(scan, [str(contract), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "redline" not in payload["red_flags"][0]
