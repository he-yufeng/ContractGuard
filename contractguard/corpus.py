"""Regression corpus: realistic sample contracts with pinned checklist verdicts.

Unit tests pin rule phrasing on snippets; the corpus pins end-to-end behavior
on full-length documents that mix compliant and violating clauses with
unrelated noise, so a checklist or parser change that alters real outcomes
fails here before release. Samples ship in pairs:

    corpus/<name>.txt    the contract text
    corpus/<name>.json   contract_type, lang, jurisdiction, expected statuses

Every starter sample is synthetic (written against the audited statute lines,
never copied from a real contract); anonymized real samples extend the same
layout as they arrive.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from contractguard.checklist import run_checklist
from contractguard.models import StatuteStatus

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"


@dataclass
class CorpusCase:
    name: str
    text: str
    contract_type: str
    lang: str
    jurisdiction: str
    expect: dict[str, StatuteStatus]
    note: str = ""


@dataclass
class CorpusMismatch:
    case: str
    rule_id: str
    expected: StatuteStatus
    actual: StatuteStatus


@dataclass
class CorpusReport:
    cases: int = 0
    checks: int = 0
    mismatches: list[CorpusMismatch] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.mismatches


def load_corpus(root: Path = CORPUS_DIR) -> list[CorpusCase]:
    cases: list[CorpusCase] = []
    for json_path in sorted(root.glob("*.json")):
        meta = json.loads(json_path.read_text(encoding="utf-8"))
        text_path = json_path.with_suffix(".txt")
        if not text_path.exists():
            raise FileNotFoundError(f"corpus case {json_path.name} has no matching .txt")
        cases.append(
            CorpusCase(
                name=json_path.stem,
                text=text_path.read_text(encoding="utf-8"),
                contract_type=meta["contract_type"],
                lang=meta["lang"],
                jurisdiction=meta.get("jurisdiction", "auto"),
                expect={rule: StatuteStatus[status] for rule, status in meta["expect"].items()},
                note=meta.get("note", ""),
            )
        )
    return cases


def run_corpus(root: Path = CORPUS_DIR) -> CorpusReport:
    report = CorpusReport()
    for case in load_corpus(root):
        report.cases += 1
        actual = {
            check.rule_id: check.status
            for check in run_checklist(case.text, case.contract_type, case.lang, jurisdiction=case.jurisdiction)
        }
        for rule_id, expected in case.expect.items():
            report.checks += 1
            got = actual.get(rule_id)
            if got is None:
                raise KeyError(f"{case.name}: {rule_id} did not run for {case.jurisdiction}/{case.contract_type}")
            if got != expected:
                report.mismatches.append(
                    CorpusMismatch(case=case.name, rule_id=rule_id, expected=expected, actual=got)
                )
    return report
