from pathlib import Path

from contractguard.batch import (
    BatchItem,
    analyze_paths,
    discover_contracts,
    summarize_batch,
)
from contractguard.models import AnalysisResult, ContractType


def _result(grade: str, score: int, reds: int = 0, warns: int = 0) -> AnalysisResult:
    issue = {
        "title": "x",
        "severity": "red",
        "clause": "c",
        "quote": "q",
        "explanation": "e",
        "suggestion": "s",
    }
    warn = {**issue, "severity": "yellow"}
    return AnalysisResult(
        contract_type=ContractType.UNKNOWN,
        summary="s",
        fairness_score=score,
        fairness_grade=grade,
        red_flags=[issue] * reds,
        warnings=[warn] * warns,
    )


def test_discover_contracts_in_directory_recursive_sorted_and_filtered(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.pdf").write_text("b")
    (tmp_path / "notes.png").write_text("not a contract")  # unsupported -> excluded
    nested = tmp_path / "sub"
    nested.mkdir()
    (nested / "c.docx").write_text("c")

    found = discover_contracts(tmp_path)

    assert [p.name for p in found] == ["a.txt", "b.pdf", "c.docx"]


def test_discover_contracts_single_file_returned_as_is(tmp_path):
    f = tmp_path / "lease.txt"
    f.write_text("lease")
    assert discover_contracts(f) == [f]


def test_analyze_paths_isolates_per_file_errors():
    def fake_analyze(path: Path) -> AnalysisResult:
        if path.name == "bad.txt":
            raise ValueError("unreadable")
        return _result("B", 80)

    items = analyze_paths(
        [Path("good.txt"), Path("bad.txt"), Path("also_good.txt")],
        fake_analyze,
    )

    assert [it.ok for it in items] == [True, False, True]
    assert items[1].error == "unreadable"
    assert items[1].result is None
    # one bad file must not stop the others from being analyzed
    assert items[2].ok


def test_analyze_paths_invokes_progress_callback_for_every_item():
    seen: list[str] = []
    analyze_paths(
        [Path("one.txt"), Path("two.txt")],
        lambda p: _result("A", 95),
        on_result=lambda item: seen.append(item.path),
    )
    assert seen == ["one.txt", "two.txt"]


def test_summarize_batch_aggregates_grades_and_issue_counts():
    items = [
        BatchItem(path="a.txt", result=_result("A", 95, reds=0, warns=1)),
        BatchItem(path="b.txt", result=_result("C", 50, reds=2, warns=3)),
        BatchItem(path="c.txt", result=_result("A", 90, reds=1, warns=0)),
        BatchItem(path="d.txt", error="boom"),
    ]

    summary = summarize_batch(items)

    assert summary.total == 4
    assert summary.succeeded == 3
    assert summary.failed == 1
    assert summary.total_red_flags == 3
    assert summary.total_warnings == 4
    assert summary.grades == {"A": 2, "C": 1}
