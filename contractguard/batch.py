"""Batch scanning: analyze several contracts in one run and aggregate the results."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from contractguard.models import AnalysisResult

# The document types parser.extract_text knows how to read.
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx", ".txt", ".md", ".rtf"})


@dataclass
class BatchItem:
    """One contract's place in a batch run: its result, or the error that stopped it."""

    path: str
    result: AnalysisResult | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.result is not None


@dataclass
class BatchSummary:
    """Aggregate view across a batch run."""

    total: int
    succeeded: int
    failed: int
    total_red_flags: int
    total_warnings: int
    grades: dict[str, int] = field(default_factory=dict)  # fairness grade -> count


def discover_contracts(path: str | Path) -> list[Path]:
    """Find the contract files to scan.

    A directory is searched recursively for files whose extension is supported;
    a single file path is returned as-is (so an explicit, oddly-named file is
    still honoured). Results are sorted for deterministic ordering.
    """
    p = Path(path)
    if p.is_dir():
        return sorted(
            f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        )
    return [p]


def analyze_paths(
    paths: Iterable[Path],
    analyze_fn: Callable[[Path], AnalysisResult],
    on_result: Callable[[BatchItem], None] | None = None,
) -> list[BatchItem]:
    """Run ``analyze_fn`` on each path, isolating per-file failures.

    A failure on one contract (unreadable file, API error, ...) is captured on
    that ``BatchItem`` and does not abort the rest of the batch — the whole point
    of batch scanning is that one bad file doesn't sink the run. ``on_result`` is
    an optional callback invoked after each item, e.g. to print progress.
    """
    items: list[BatchItem] = []
    for path in paths:
        try:
            item = BatchItem(path=str(path), result=analyze_fn(path))
        except Exception as exc:  # noqa: BLE001 - per-file isolation is intentional
            item = BatchItem(path=str(path), error=str(exc))
        items.append(item)
        if on_result is not None:
            on_result(item)
    return items


def summarize_batch(items: list[BatchItem]) -> BatchSummary:
    """Aggregate stats (counts, fairness grades, total issues) across a batch run."""
    grades: dict[str, int] = {}
    total_red_flags = 0
    total_warnings = 0
    succeeded = 0
    for item in items:
        if not item.ok or item.result is None:
            continue
        succeeded += 1
        grade = item.result.fairness_grade
        grades[grade] = grades.get(grade, 0) + 1
        total_red_flags += len(item.result.red_flags)
        total_warnings += len(item.result.warnings)
    return BatchSummary(
        total=len(items),
        succeeded=succeeded,
        failed=len(items) - succeeded,
        total_red_flags=total_red_flags,
        total_warnings=total_warnings,
        grades=grades,
    )
