"""Contract comparison: diff two analyzed versions of the same contract."""

from __future__ import annotations

from dataclasses import dataclass, field

from contractguard.models import AnalysisResult, Issue


@dataclass
class ContractComparison:
    """What changed between an earlier and a later version of a contract."""

    score_before: int
    score_after: int
    grade_before: str
    grade_after: str
    added_red_flags: list[Issue] = field(default_factory=list)
    resolved_red_flags: list[Issue] = field(default_factory=list)
    added_warnings: list[Issue] = field(default_factory=list)
    resolved_warnings: list[Issue] = field(default_factory=list)

    @property
    def score_delta(self) -> int:
        """Positive when the later version is fairer."""
        return self.score_after - self.score_before


def _diff_by_title(before: list[Issue], after: list[Issue]) -> tuple[list[Issue], list[Issue]]:
    """Match issues by title and return ``(added, resolved)``.

    Added = present in *after* but not *before*; resolved = present in *before*
    but not *after*. Issues carried over unchanged appear in neither list.
    """
    before_titles = {issue.title for issue in before}
    after_titles = {issue.title for issue in after}
    added = [issue for issue in after if issue.title not in before_titles]
    resolved = [issue for issue in before if issue.title not in after_titles]
    return added, resolved


def compare_results(before: AnalysisResult, after: AnalysisResult) -> ContractComparison:
    """Diff two analysis results: which issues were added or resolved, and how the
    fairness score moved between the two versions."""
    added_red, resolved_red = _diff_by_title(before.red_flags, after.red_flags)
    added_warn, resolved_warn = _diff_by_title(before.warnings, after.warnings)
    return ContractComparison(
        score_before=before.fairness_score,
        score_after=after.fairness_score,
        grade_before=before.fairness_grade,
        grade_after=after.fairness_grade,
        added_red_flags=added_red,
        resolved_red_flags=resolved_red,
        added_warnings=added_warn,
        resolved_warnings=resolved_warn,
    )
