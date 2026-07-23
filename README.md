<div align="center">

<img src="docs/banner.png" alt="ContractGuard — never sign a bad contract again" width="100%">

Upload any contract → get red flags, unfair terms, and plain-English explanations in seconds.

[![PyPI](https://img.shields.io/pypi/v/contractguardian.svg)](https://pypi.org/project/contractguardian/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/he-yufeng/ContractGuard/actions/workflows/ci.yml/badge.svg)](https://github.com/he-yufeng/ContractGuard/actions)

**[English](README.md) · [中文](README_CN.md)** &nbsp;·&nbsp; [Demo](#demo) · [Quick Start](#quick-start) · [How It Works](#how-it-works)

</div>

---

## Why ContractGuard?

Every year, millions of people sign contracts they don't fully understand — apartment leases with hidden penalties, employment agreements with overly broad non-competes, NDAs that silently strip away your rights. Hiring a lawyer costs $300-500/hour. Most people just sign and hope for the best.

**ContractGuard** changes that. It's an open-source AI agent that reads every clause of your contract, flags problems in plain language, and tells you exactly what to negotiate — all in under 30 seconds.

**What makes it different from ChatGPT?**
- **Structured analysis**, not a wall of text — you get categorized red flags, warnings, protections, and a fairness score
- **Actionable suggestions** for every issue found — not just "this is bad" but "change it to this"
- **Consistent output format** via Pydantic models — easy to integrate into other tools
- **CLI-first design** — one command, beautiful terminal output, no browser needed
- **Works with any LLM** — OpenRouter, OpenAI, Ollama (fully local/private)

## Demo

```bash
contractguard scan my-lease.pdf
```

```
✔ Parsed my-lease.pdf (4,521 characters)

⬤ RED FLAGS (5 found)
==================================================

  1. Non-refundable security deposit
     Clause: Section 3
     "The security deposit is non-refundable and shall
      be retained by Landlord upon termination"
     Most states require deposits to be refundable.
     This clause is likely illegal in California.
     Suggestion: Remove "non-refundable" language.

  2. Unlimited landlord access without notice
     Clause: Section 5
     "Landlord shall have the right to enter the Property
      at any time, with or without notice"
     California law requires 24-hour written notice.
     Suggestion: Add "with 24 hours written notice"

  … 3 more red flags, 3 warnings, 2 protections, 4 missing protections …

FAIRNESS SCORE: D (28/100)
  5 red flags  3 warnings  2 protections  4 missing
```

## Quick Start

### 1. Install

```bash
pip install contractguardian
```

### 2. Set up your API key

ContractGuard works with any OpenAI-compatible API. Pick one:

**Option A: OpenRouter (recommended)** — access to Claude, GPT-4, DeepSeek, Gemini, and 100+ models through a single API key:

```bash
export OPENROUTER_API_KEY=sk-or-...
```

**Option B: OpenAI directly:**

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1
```

**Option C: Local models via Ollama** — your contract data never leaves your machine:

```bash
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
```

### 3. Scan a contract

```bash
contractguard scan my-contract.pdf
```

That's it. Three steps, under 60 seconds.

## Usage

```bash
# Scan a PDF, DOCX, or TXT
contractguard scan lease.pdf

# Pick any OpenRouter / OpenAI / Ollama model
contractguard scan contract.pdf --model openai/gpt-4o

# Export a markdown report, or structured JSON for scripting
contractguard scan contract.pdf --output report.md
contractguard scan contract.pdf --json --output report.json

# Scan a whole folder, or diff two versions of a contract
contractguard batch ./contracts/ --output-dir reports/
contractguard compare lease-v1.pdf lease-v2.pdf
```

### Python API

```python
from contractguard.analyzer import analyze_contract
from contractguard.parser import extract_text

result = analyze_contract(extract_text("my-lease.pdf"))
print(f"{result.fairness_grade} ({result.fairness_score}/100)")
for flag in result.red_flags:
    print(f"- {flag.title} ({flag.clause}): {flag.suggestion}")
```

`--json` emits the full structured result — contract type, parties, key terms, red flags, warnings, protections, and fairness score — as a Pydantic-backed object ready to pipe into other tools.

## Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | Text-based PDFs. Scanned/image-based PDFs require OCR (coming soon). |
| Word | `.docx` | Microsoft Word documents |
| Plain Text | `.txt` | Plain text files |
| Markdown | `.md` | Markdown files |
| Rich Text | `.rtf` | Rich Text Format files |

## Supported Contract Types

ContractGuard automatically detects the contract type and tailors its analysis accordingly. Each type has specific red flags and industry-standard protections it checks for:

| Contract Type | What ContractGuard Checks |
|---|---|
| **Residential Leases** | Rent increases, deposit refundability, maintenance obligations, landlord access rights, early termination penalties, habitability guarantees |
| **NDAs / Confidentiality** | Scope of "confidential information" (too broad?), duration, non-solicitation, non-compete, carve-outs for prior knowledge, return/destruction of materials |
| **Employment Contracts** | Non-compete scope & duration, IP assignment (does employer own your side projects?), termination notice period, severance, at-will vs. for-cause, benefits |
| **Freelance / Contractor** | Payment terms & schedule, kill fees, IP ownership, indemnification, scope creep protections, late payment penalties |
| **SaaS Terms of Service** | Data ownership & portability, auto-renewal & cancellation, SLA guarantees, limitation of liability, unilateral modification rights |
| **Loan Agreements** | Interest rate (fixed vs. variable), prepayment penalties, default triggers, personal guarantee scope, collateral requirements |
| **Purchase Agreements** | Warranty terms, return/refund policy, liability limits, dispute resolution (arbitration vs. court), force majeure |

## How It Works

![ContractGuard pipeline](docs/architecture.png)

1. **Parse** — Extracts text from your document (PDF, DOCX, TXT). For PDFs, uses `pdfplumber` to handle complex layouts. For DOCX, uses `python-docx` to read all paragraphs.

2. **Detect** — Sends the extracted text to the LLM, which automatically identifies the contract type (lease, NDA, employment, etc.) and adjusts its analysis strategy.

3. **Analyze** — The AI agent reviews every clause and categorizes findings into four groups:
   - **Red Flags** — Serious issues that could cause financial harm, legal liability, or loss of rights. These are things you should push back on before signing.
   - **Warnings** — Moderate concerns that are worth discussing but aren't necessarily deal-breakers. Common in many contracts but still worth knowing about.
   - **Protections** — Good clauses that protect your interests. These are things the contract got right.
   - **Missing Protections** — Standard clauses that are absent from the contract. Their absence may leave you exposed.

4. **Score** — Generates an overall fairness grade from A+ (excellent, fair to both parties) to F (heavily one-sided, many red flags). The score is based on the number and severity of issues found, balanced against protections present.

5. **Verify** — A deterministic statute checklist runs alongside the LLM, checking the rules where a wrong answer is a violation, not an opinion: probation length and pay caps, penalty scope, non-compete duration and compensation (PRC Labor Contract Law), earnest-money ratio and lease-term caps (PRC Civil Code). Each check returns violation / ok / unknown, and "unknown" is reported honestly when the clause is missing instead of passing as compliance. Disable with `--no-checklist`.

6. **Report** — Outputs results as a beautiful Rich-formatted terminal report, or exports to Markdown/JSON/HTML for sharing or further processing.

## Configuration

### LLM Providers

ContractGuard uses the OpenAI-compatible API format, so it works with virtually any LLM provider:

| Provider | Setup | Best For |
|----------|-------|----------|
| **OpenRouter** | `export OPENROUTER_API_KEY=sk-or-...` | Access to 100+ models through one API key |
| **OpenAI** | `export OPENAI_API_KEY=sk-...` + `export OPENAI_BASE_URL=https://api.openai.com/v1` | Direct access to GPT-4o, o1, etc. |
| **Anthropic (via OpenRouter)** | Use `--model anthropic/claude-sonnet-4` | Best reasoning for complex contracts |
| **Ollama (local)** | `export OPENAI_BASE_URL=http://localhost:11434/v1` | Maximum privacy — data never leaves your machine |
| **Azure OpenAI** | Set `OPENAI_BASE_URL` to your Azure endpoint | Enterprise compliance |
| **Any OpenAI-compatible API** | Set `OPENAI_BASE_URL` and `OPENAI_API_KEY` | Self-hosted models, vLLM, etc. |

Default model is `anthropic/claude-sonnet-4`. `google/gemini-2.5-pro` handles very long contracts (1M context), `deepseek/deepseek-chat` is the budget pick, and any Ollama model keeps your data local.

## FAQ

**Is this legal advice?**
No. ContractGuard is an educational tool for understanding contract terms in plain language, not a substitute for a licensed attorney.

**Is my contract data sent to the cloud?**
Only to the LLM provider you configure. For full privacy, use a local model via Ollama — the text never leaves your machine. ContractGuard itself stores and logs nothing.

**What's the maximum contract length?**
About 30,000 tokens (~60 pages); longer documents are truncated. Use a large-context model like `google/gemini-2.5-pro` for very long contracts.

**Can I use it in CI/CD?**
Yes. `--json` gives parseable output; exit code is 0 on success, 1 on error. E.g. `contractguard scan contract.pdf --json | jq '.red_flags | length'`.

## Roadmap

**Shipped:** batch scanning (analyze many contracts in one run) and contract comparison (diff two versions and surface what changed, clause by clause).

**Planned:**

- **OCR for scanned PDFs** — handle image-only contracts, not just text PDFs, which is where a lot of real paperwork actually lives.
- **Jurisdiction-aware analysis** — judge clauses against a chosen jurisdiction (US state law, EU, China), since whether a term is risky depends on where it's enforced.
- **Clause-by-clause negotiation drafts** — for each red flag, draft suggested replacement language, turning the report into the start of a redline.
- **A web UI** — a Streamlit/Gradio front end for people who won't touch a CLI, with the same local-only handling.
- **Pre-built contract templates** — a few common contract types with known red flags, useful both as a starting point and as a test corpus.

## Related Projects

ContractGuard is one of my applied agent projects. A few others worth a look:

- **[CoreCoder](https://github.com/he-yufeng/CoreCoder)** — want to understand how a coding agent really works? Read the whole ~1k-line engine end to end, not a black box.
- **[RepoWiki](https://github.com/he-yufeng/RepoWiki)** — dropped into an unfamiliar codebase? It gives you a guided wiki and a where-to-start reading path, a self-hostable DeepWiki alternative.
- **[FindJobs-Agent](https://github.com/he-yufeng/FindJobs-Agent)** — stop sifting job boards by hand: it ranks postings against your resume and runs mock interviews.
- **[GitSense](https://github.com/he-yufeng/GitSense)** — want to contribute to open source? It finds issues worth your time and gauges whether your PR will get merged.
- **[CodeABC](https://github.com/he-yufeng/CodeABC)** — understand any codebase even if you don't code, built for non-programmers.

## Contributing

Contributions are welcome! Here's how you can help:

- **Report bugs** — Open an [issue](https://github.com/he-yufeng/ContractGuard/issues) with the contract type and expected behavior
- **Add contract samples** — More sample contracts for testing (with intentional red flags)
- **Improve prompts** — Better LLM prompts for more accurate analysis
- **Add languages** — Test with contracts in different languages and report results
- **Build integrations** — MCP server, VS Code extension, Slack bot, etc.

## License

[MIT](LICENSE) — use it however you want.
