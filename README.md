<div align="center">

# ContractGuard

**AI-powered contract review agent — never sign a bad contract again.**

Upload any contract → get red flags, unfair terms, and plain-English explanations in seconds.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/he-yufeng/ContractGuard/actions/workflows/ci.yml/badge.svg)](https://github.com/he-yufeng/ContractGuard/actions)

**[English](README.md) | [中文](README_CN.md)**

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

  3. Tenant pays for structural repairs
     Clause: Section 4
     "Tenant is responsible for all maintenance and repairs
      including plumbing, electrical systems, and structural elements"
     Structural repairs are typically the landlord's responsibility.
     Suggestion: Limit tenant responsibility to minor maintenance only.

  4. One-sided termination clause
     Clause: Section 10
     "Landlord may terminate this Lease at any time with
      thirty (30) days' written notice for any reason"
     Tenant has no equivalent right. This creates an imbalance.
     Suggestion: Add mutual termination rights or require cause.

  5. Tenant pays landlord's attorney fees regardless of outcome
     Clause: Section 12
     "Tenant shall be responsible for all attorney's fees
      incurred by Landlord, regardless of the outcome"
     One-sided fee-shifting discourages tenants from asserting rights.
     Suggestion: Change to mutual fee-shifting (loser pays).

⚠ WARNINGS (3 found)
==================================================

  1. 90-day notice period for non-renewal
     Clause: Section 1
     Suggestion: Negotiate down to 30-60 days.

  2. 15% rent increase cap on renewal
     Clause: Section 2
     Suggestion: Negotiate a lower cap or tie to CPI.

  3. No subletting without landlord consent (may withhold for any reason)
     Clause: Section 9
     Suggestion: Add "consent shall not be unreasonably withheld."

✔ PROTECTIONS (2 found)
==================================================
  ✔ Written notice required for termination (Section 1)
  ✔ Lease modification requires written agreement from both parties (Section 13)

❓ MISSING PROTECTIONS (4)
  ✗ No habitability guarantee
  ✗ No grace period for lease violations before termination
  ✗ No limit on late fees
  ✗ No provision for return of security deposit after move-out

FAIRNESS SCORE: D (28/100)
  5 red flags  3 warnings  2 protections  4 missing
```

## Quick Start

### 1. Install

```bash
pip install contractguard
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

### CLI Commands

```bash
# Basic scan — PDF, DOCX, or TXT
contractguard scan lease.pdf
contractguard scan employment-agreement.docx
contractguard scan nda.txt

# Choose a specific model
contractguard scan contract.pdf --model openai/gpt-4o
contractguard scan contract.pdf --model anthropic/claude-sonnet-4
contractguard scan contract.pdf --model google/gemini-2.5-pro
contractguard scan contract.pdf --model llama3.1    # local via Ollama

# Export the report as a markdown file
contractguard scan contract.pdf --output report.md

# Get structured JSON output (for integrations or scripting)
contractguard scan contract.pdf --json

# Save structured JSON directly
contractguard scan contract.pdf --json --output report.json

# Pass API key directly (instead of env variable)
contractguard scan contract.pdf --api-key sk-or-...
```

### Python API

Use ContractGuard as a library in your own applications:

```python
from contractguard.analyzer import analyze_contract
from contractguard.parser import extract_text

# Step 1: Extract text from any supported document
text = extract_text("my-lease.pdf")

# Step 2: Run the AI analysis
result = analyze_contract(text)

# Step 3: Use the structured results
print(f"Contract Type: {result.contract_type.value}")
print(f"Fairness Score: {result.fairness_grade} ({result.fairness_score}/100)")
print(f"Parties: {', '.join(result.parties)}")

print(f"\n{len(result.red_flags)} Red Flags:")
for flag in result.red_flags:
    print(f"  - {flag.title} (Clause: {flag.clause})")
    print(f"    Issue: {flag.explanation}")
    print(f"    Fix: {flag.suggestion}")

print(f"\n{len(result.warnings)} Warnings:")
for warning in result.warnings:
    print(f"  - {warning.title}: {warning.explanation}")

print(f"\n{len(result.good_clauses)} Protections:")
for protection in result.good_clauses:
    print(f"  + {protection.title}: {protection.explanation}")

print(f"\n{len(result.missing_protections)} Missing Protections:")
for missing in result.missing_protections:
    print(f"  ? {missing}")

# Export to markdown
from contractguard.report import generate_markdown_report
md = generate_markdown_report(result)
with open("report.md", "w") as f:
    f.write(md)
```

### JSON Output Schema

When using `--json`, ContractGuard outputs a structured JSON object you can pipe to other tools:

```json
{
  "contract_type": "lease",
  "summary": "A 12-month residential lease with several one-sided clauses...",
  "parties": ["Apex Property Management LLC", "Tenant"],
  "key_terms": ["Duration: 12 months", "Rent: $3,200/month", "Deposit: $6,400"],
  "red_flags": [
    {
      "title": "Non-refundable security deposit",
      "severity": "red",
      "clause": "Section 3",
      "quote": "The security deposit is non-refundable...",
      "explanation": "Most states require deposits to be refundable...",
      "suggestion": "Remove non-refundable language."
    }
  ],
  "warnings": [...],
  "good_clauses": [...],
  "missing_protections": [...],
  "fairness_score": 28,
  "fairness_grade": "D"
}
```

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

1. **Parse** — Extracts text from your document (PDF, DOCX, TXT). For PDFs, uses `pdfplumber` to handle complex layouts. For DOCX, uses `python-docx` to read all paragraphs.

2. **Detect** — Sends the extracted text to the LLM, which automatically identifies the contract type (lease, NDA, employment, etc.) and adjusts its analysis strategy.

3. **Analyze** — The AI agent reviews every clause and categorizes findings into four groups:
   - **Red Flags** — Serious issues that could cause financial harm, legal liability, or loss of rights. These are things you should push back on before signing.
   - **Warnings** — Moderate concerns that are worth discussing but aren't necessarily deal-breakers. Common in many contracts but still worth knowing about.
   - **Protections** — Good clauses that protect your interests. These are things the contract got right.
   - **Missing Protections** — Standard clauses that are absent from the contract. Their absence may leave you exposed.

4. **Score** — Generates an overall fairness grade from A+ (excellent, fair to both parties) to F (heavily one-sided, many red flags). The score is based on the number and severity of issues found, balanced against protections present.

5. **Report** — Outputs results as a beautiful Rich-formatted terminal report, or exports to Markdown/JSON for sharing or further processing.

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

### Recommended Models

| Model | Quality | Speed | Cost | Notes |
|-------|---------|-------|------|-------|
| `anthropic/claude-sonnet-4` (default) | Excellent | Fast | $$ | Best balance of quality and speed |
| `openai/gpt-4o` | Excellent | Fast | $$ | Strong alternative |
| `google/gemini-2.5-pro` | Excellent | Medium | $$ | Great for long contracts (1M context) |
| `deepseek/deepseek-chat` | Good | Fast | $ | Budget-friendly option |
| `llama3.1` (via Ollama) | Good | Varies | Free | Fully private, runs locally |

## Try It with Sample Contracts

The repo includes sample contracts intentionally loaded with red flags for testing:

```bash
git clone https://github.com/he-yufeng/ContractGuard.git
cd ContractGuard
pip install -e .

export OPENROUTER_API_KEY=sk-or-...

# Sample lease — has 5+ red flags including non-refundable deposit,
# unlimited landlord access, and one-sided termination
contractguard scan examples/sample_lease.txt

# Sample NDA — has perpetual confidentiality obligations
# and a broad non-solicitation clause
contractguard scan examples/sample_nda.txt
```

## Common Red Flags ContractGuard Catches

Here are some real examples of issues ContractGuard is designed to detect:

**Leases:**
- Non-refundable security deposits (illegal in many jurisdictions)
- Landlord can enter without notice (most laws require 24-48 hours)
- Tenant responsible for structural repairs (usually landlord's job)
- Auto-renewal with no opt-out window
- Excessive late fees

**Employment:**
- Non-compete that's too broad (geographic scope, duration, industry)
- IP assignment that covers personal/side projects
- At-will termination with no severance
- Forced arbitration with company-selected arbitrator

**NDAs:**
- "Confidential information" defined so broadly it covers everything
- Perpetual confidentiality obligations (no expiration)
- Non-solicitation disguised within an NDA
- No carve-out for independently developed information

**SaaS/ToS:**
- Provider can change terms unilaterally at any time
- No data portability or export on termination
- Limitation of liability that caps damages below subscription cost
- Forced arbitration with class action waiver

## FAQ

**Is this legal advice?**
No. ContractGuard is an educational tool that helps you understand contract terms in plain language. It is not a substitute for qualified legal counsel. Always consult a licensed attorney for binding legal decisions.

**Is my contract data sent to the cloud?**
The contract text is sent to whichever LLM provider you configure (OpenRouter, OpenAI, etc.) for analysis. If privacy is a concern, use a local model via Ollama — your data will never leave your machine. ContractGuard itself does not store, log, or transmit your data anywhere.

**How accurate is it?**
ContractGuard uses state-of-the-art LLMs (Claude Sonnet, GPT-4o) which are highly capable at legal text analysis. In testing with sample contracts, it consistently identifies major red flags that match professional legal review. However, it may miss subtle jurisdictional nuances or complex multi-clause interactions that an experienced attorney would catch. Use it as a first-pass filter to know what questions to ask, not as a final opinion.

**What languages are supported?**
ContractGuard works with contracts in any language the underlying LLM supports. English produces the best results. Chinese, Spanish, French, German, Japanese, and Korean contracts also work well with models like Claude and GPT-4o.

**Can I use it for business / commercial purposes?**
Yes. ContractGuard is MIT licensed — you can use it freely in personal and commercial projects, integrate it into your SaaS product, or modify it however you want.

**What's the maximum contract length?**
ContractGuard supports contracts up to ~30,000 tokens (~120,000 characters / ~60 pages). Longer documents are automatically truncated. For very long contracts, consider using a model with a large context window like `google/gemini-2.5-pro` (1M tokens).

**Can I use it in CI/CD or automated pipelines?**
Yes. Use `--json` to get structured output that can be parsed by other tools. Exit code is 0 on success, 1 on error. Example: `contractguard scan contract.pdf --json | jq '.red_flags | length'`

## Integrations

- **Bindu (A2A agent)** — run ContractGuard as a discoverable, DID-identified microservice that other AI agents can call over the [A2A protocol](https://github.com/getbindu/Bindu). Optional pay-per-scan via x402 (USDC on Base). See [examples/bindu](examples/bindu/).

## Roadmap

- [ ] OCR support for scanned PDF contracts
- [ ] Batch scanning (analyze multiple contracts at once)
- [ ] Contract comparison (diff two versions of a contract)
- [ ] Clause-by-clause negotiation draft generation
- [ ] Web UI (Streamlit/Gradio)
- [ ] Pre-built contract templates for common use cases
- [ ] Jurisdiction-aware analysis (US state laws, EU regulations, China)

## Contributing

Contributions are welcome! Here's how you can help:

- **Report bugs** — Open an [issue](https://github.com/he-yufeng/ContractGuard/issues) with the contract type and expected behavior
- **Add contract samples** — More sample contracts for testing (with intentional red flags)
- **Improve prompts** — Better LLM prompts for more accurate analysis
- **Add languages** — Test with contracts in different languages and report results
- **Build integrations** — MCP server, VS Code extension, Slack bot, etc.

## License

[MIT](LICENSE) — use it however you want.

---

<div align="center">

**If ContractGuard saved you from a bad contract, consider giving it a star!**

[Report a Bug](https://github.com/he-yufeng/ContractGuard/issues) · [Request a Feature](https://github.com/he-yufeng/ContractGuard/issues)

</div>
