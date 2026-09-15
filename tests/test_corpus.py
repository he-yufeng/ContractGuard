"""The release-corpus gate: full-length sample contracts must keep their pinned verdicts."""

from __future__ import annotations

from contractguard.corpus import load_corpus, run_corpus


def test_corpus_has_no_mismatches():
    report = run_corpus()
    details = "\n".join(
        f"  {m.case}: {m.rule_id} expected {m.expected.name} got {m.actual.name}" for m in report.mismatches
    )
    assert report.ok, f"corpus regressions:\n{details}"


def test_every_corpus_case_covers_multiple_rules():
    # a corpus case that pins one rule is a snippet test wearing a trench coat
    for case in load_corpus():
        assert len(case.expect) >= 3, f"{case.name} pins {len(case.expect)} rules"
