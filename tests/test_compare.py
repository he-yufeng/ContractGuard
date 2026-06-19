from contractguard.compare import compare_results
from contractguard.models import AnalysisResult, ContractType, Issue, Severity


def _issue(title: str, severity: Severity = Severity.RED) -> Issue:
    return Issue(
        title=title,
        severity=severity,
        clause="c",
        quote="q",
        explanation="e",
        suggestion="s",
    )


def _result(score: int, grade: str, reds: list[str], warns: list[str]) -> AnalysisResult:
    return AnalysisResult(
        contract_type=ContractType.LEASE,
        summary="s",
        fairness_score=score,
        fairness_grade=grade,
        red_flags=[_issue(t, Severity.RED) for t in reds],
        warnings=[_issue(t, Severity.YELLOW) for t in warns],
    )


def test_compare_identifies_added_and_resolved_issues():
    before = _result(40, "C", reds=["Non-refundable deposit", "Auto-renewal"], warns=["Late fee"])
    after = _result(75, "B", reds=["Auto-renewal"], warns=["Late fee", "Short cure period"])

    cmp = compare_results(before, after)

    # "Non-refundable deposit" was fixed; "Auto-renewal" carried over (neither list)
    assert [i.title for i in cmp.resolved_red_flags] == ["Non-refundable deposit"]
    assert cmp.added_red_flags == []
    # a new warning appeared; the existing one carried over
    assert [i.title for i in cmp.added_warnings] == ["Short cure period"]
    assert cmp.resolved_warnings == []


def test_compare_reports_score_and_grade_movement():
    before = _result(40, "C", reds=["x"], warns=[])
    after = _result(75, "B", reds=[], warns=[])

    cmp = compare_results(before, after)

    assert cmp.score_before == 40
    assert cmp.score_after == 75
    assert cmp.score_delta == 35
    assert cmp.grade_before == "C"
    assert cmp.grade_after == "B"


def test_compare_detects_regressions():
    before = _result(80, "B", reds=[], warns=["Late fee"])
    after = _result(55, "C", reds=["Hidden penalty"], warns=["Late fee"])

    cmp = compare_results(before, after)

    assert [i.title for i in cmp.added_red_flags] == ["Hidden penalty"]
    assert cmp.score_delta == -25  # got worse
