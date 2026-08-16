"""--json output must stay valid JSON when piped (no Rich soft-wrapping)."""

import json

from click.testing import CliRunner

from contractguard.cli import scan
from contractguard.models import AnalysisResult, ContractType


def test_json_output_survives_piping(tmp_path, monkeypatch):
    contract = tmp_path / "c.txt"
    contract.write_text("a contract", encoding="utf-8")

    monkeypatch.setattr(
        "contractguard.parser.extract_text", lambda *a, **k: "the contract text"
    )

    long_summary = "x" * 300  # wraps at console width 80 under Rich
    monkeypatch.setattr(
        "contractguard.analyzer.analyze_contract",
        lambda **_: AnalysisResult(
            contract_type=ContractType.UNKNOWN,
            summary=long_summary,
            fairness_score=50,
            fairness_grade="C",
        ),
    )
    monkeypatch.setattr(
        "contractguard.checklist.run_checklist", lambda *a, **k: []
    )

    result = CliRunner().invoke(scan, [str(contract), "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)  # raises if Rich wrapped any line
    assert parsed["summary"] == long_summary
    # progress chrome went to stderr, keeping stdout pipe-clean
    assert "Parsed" in result.stderr
