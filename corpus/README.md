# Release corpus

Full-length sample contracts with pinned checklist verdicts. The unit tests
pin rule phrasing on snippets; this corpus pins end-to-end behavior on
realistic documents that mix compliant and violating clauses with section
headers and unrelated boilerplate, so a checklist or parser change that
alters real outcomes fails before release.

Layout: each case is a pair

```
<name>.txt    the contract text
<name>.json   contract_type, lang, jurisdiction, expect (rule_id -> status), note
```

Run it:

```bash
pytest tests/test_corpus.py          # the gate (blocking)
python -c "from contractguard.corpus import run_corpus; print(run_corpus().ok)"
```

The starter six are synthetic, written against the audited statute lines
(CA Civil Code §1950.5/§1954 and PRC Labor Contract Law) and never copied
from a real contract. Anonymized real samples extend the same layout as they
arrive; every case must pin at least three rules so it stays a document-level
test rather than a snippet in disguise.
