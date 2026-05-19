# ContractGuard × Bindu — A2A agent integration

Run ContractGuard as a discoverable, DID-identified microservice that other AI
agents can call over the [A2A](https://github.com/getbindu/Bindu) JSON-RPC
protocol. Same analyzer, same `AnalysisResult` schema — now reachable on the
network with a verifiable identity and (optionally) pay-per-scan via x402.

## Why pair them?

ContractGuard is a great library, CLI, and Gradio app — but every integration
beyond that (Slack bot, VS Code extension, an orchestrator that chains it
after a "find me a lease" agent) ends up rebuilding the same plumbing: an
HTTP endpoint, an identity, an auth story, a way to charge for it.

[Bindu](https://github.com/getbindu/Bindu) is the plumbing. Wrap the analyzer
in one `bindufy(config, handler)` call and you get:

- **Discoverable agent card** at `/.well-known/agent.json` — agent
  marketplaces and orchestrators can find ContractGuard and know what it
  does.
- **DID-based identity** (`did:bindu:…`) — every analysis is attributable to
  a cryptographically-verifiable agent. Bindu signs each result artifact
  with the agent's Ed25519 key (the signature shows up as
  `did.message.signature` on the artifact part), so a contract review can be
  presented as tamper-evidence: "ContractGuard `did:bindu:…` said this at
  timestamp T."
- **A2A JSON-RPC** over HTTP — peers call `message/send` with the contract
  as a `text` part and the handler returns the existing structured
  `AnalysisResult` as JSON.
- **Pay-per-scan via x402** — uncomment the `execution_cost` block in
  `agent.py` and the agent demands a USDC micropayment on Base before
  responding. No Stripe account, no login flow, no SaaS dashboard.
- **OAuth2 / mTLS** (optional) for B2B deployments.

The integration is purely additive: nothing in `contractguard/` changes,
`bindu` is not a required dependency, and the CLI / Python API / Gradio UI
all still work exactly as before.

## Setup

```bash
# From the ContractGuard repo root
pip install -e .            # core contractguard
pip install bindu           # adds the bindufy() wrapper

cp examples/bindu/.env.example .env
# edit .env: set OPENROUTER_API_KEY=sk-or-...
```

## Run

```bash
python examples/bindu/agent.py
```

You should see Bindu's startup banner and the agent listening on
<http://localhost:3773>. Three useful endpoints:

| Endpoint | What it is |
|---|---|
| `GET  /.well-known/agent.json` | Agent card — name, description, DID, capabilities |
| `GET  /.well-known/did.json`   | DID document with the agent's public key |
| `POST /`                       | A2A JSON-RPC endpoint (use `method: "message/send"`) |

Quick health check:

```bash
curl -s http://localhost:3773/health | python -m json.tool
```

## Try it out

The A2A JSON-RPC `id` and all message-level IDs must be UUIDs. Examples
below use zero-UUIDs for readability — generate real ones with `uuidgen` for
production.

### One-shot end-to-end script

This script analyses the included `examples/sample_lease.txt` and prints the
final analysis JSON. Copy-paste it after starting the agent:

```bash
TASK_ID="00000000-0000-0000-0000-000000000013"

# 1. Send the contract
python3 -c "
import json
contract = open('examples/sample_lease.txt').read()
print(json.dumps({
  'jsonrpc':'2.0','id':'00000000-0000-0000-0000-000000000001',
  'method':'message/send',
  'params':{
    'message':{
      'role':'user','kind':'message',
      'messageId':'00000000-0000-0000-0000-000000000011',
      'contextId':'00000000-0000-0000-0000-000000000012',
      'taskId':'$TASK_ID',
      'parts':[{'kind':'text','text': contract}],
    },
    'configuration':{'acceptedOutputModes':['application/json']},
  }
}))" | curl -sS http://localhost:3773/ -H 'Content-Type: application/json' -d @- > /dev/null

# 2. Poll until completed (typically <10s)
while true; do
  state=$(curl -sS http://localhost:3773/ -H 'Content-Type: application/json' -d "{
    \"jsonrpc\":\"2.0\",\"id\":\"00000000-0000-0000-0000-000000000002\",
    \"method\":\"tasks/get\",\"params\":{\"taskId\":\"$TASK_ID\"}}" \
    | python3 -c "import json,sys;print(json.load(sys.stdin)['result']['status']['state'])")
  echo "state: $state"
  [ "$state" = "completed" ] && break
  sleep 2
done

# 3. Pretty-print the analysis JSON from the result artifact
curl -sS http://localhost:3773/ -H 'Content-Type: application/json' -d "{
  \"jsonrpc\":\"2.0\",\"id\":\"00000000-0000-0000-0000-000000000003\",
  \"method\":\"tasks/get\",\"params\":{\"taskId\":\"$TASK_ID\"}}" \
  | python3 -c "
import json,sys
r = json.load(sys.stdin)
art = r['result']['artifacts'][0]['parts'][0]
print('DID signature:', art['metadata']['did.message.signature'][:40], '...')
print()
print(json.dumps(json.loads(art['text']), indent=2))
"
```

### Sample request body

`message/send` accepts an A2A JSON-RPC envelope. The handler reads every
`text` part on the user message and treats it as the contract:

```json
{
  "jsonrpc": "2.0",
  "id": "00000000-0000-0000-0000-000000000001",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "kind": "message",
      "messageId": "00000000-0000-0000-0000-000000000011",
      "contextId": "00000000-0000-0000-0000-000000000012",
      "taskId":    "00000000-0000-0000-0000-000000000013",
      "parts": [
        { "kind": "text", "text": "<paste the full contract text here>" }
      ]
    },
    "configuration": { "acceptedOutputModes": ["application/json"] }
  }
}
```

`message/send` is async — the immediate response is a task object with
state `submitted`. The actual analysis arrives on the result artifact a few
seconds later; fetch it with `tasks/get` (params: `{"taskId": "..."}`).

### Sample response

After polling, `tasks/get` returns the completed task. The analysis JSON
lives on the result artifact's first text part; the part metadata carries
the DID signature over the result:

```json
{
  "jsonrpc": "2.0",
  "id": "00000000-0000-0000-0000-000000000003",
  "result": {
    "id":         "00000000-0000-0000-0000-000000000013",
    "context_id": "00000000-0000-0000-0000-000000000012",
    "kind": "task",
    "status": { "state": "completed", "timestamp": "2026-05-19T00:00:00Z" },
    "artifacts": [
      {
        "artifact_id": "<uuid>",
        "name": "result",
        "parts": [
          {
            "kind": "text",
            "text": "<the AnalysisResult JSON, stringified — shown below>",
            "metadata": {
              "did.message.signature": "AA1sdxDhbTkDDHKD3tJWCDGDo9Lk5VdLjWYg…"
            }
          }
        ]
      }
    ]
  }
}
```

Parsing the artifact's `text` field yields the `AnalysisResult` — captured
below by running this agent against `examples/sample_lease.txt`. Arrays
trimmed for readability; the full output contained 7 red flags, 4
warnings, 2 protections, and 7 missing protections.

```json
{
  "contract_type": "lease",
  "summary": "This is a 12-month residential lease for an apartment in San Francisco with automatic renewal. The contract heavily favors the landlord with numerous tenant-unfriendly terms including non-refundable deposits, unlimited landlord access, and broad tenant liability.",
  "parties": [
    "Apex Property Management LLC (Landlord)",
    "Tenant"
  ],
  "key_terms": [
    "Duration: 12 months with auto-renewal",
    "Rent: $3,200/month",
    "Security deposit: $6,400 (non-refundable)",
    "..."
  ],
  "red_flags": [
    {
      "title": "Non-refundable security deposit",
      "severity": "red",
      "clause": "Section 3",
      "quote": "The security deposit is non-refundable and shall be retained by Landlord upon termination of this Lease for any reason, including normal wear and tear.",
      "explanation": "This violates California law. Security deposits must be refundable minus actual damages beyond normal wear and tear. A blanket non-refundable deposit is illegal in California.",
      "suggestion": "Demand this clause be removed and replaced with standard California security deposit terms allowing refund minus legitimate damages."
    },
    {
      "title": "Unlimited landlord access without notice",
      "severity": "red",
      "clause": "Section 5",
      "quote": "Landlord and Landlord's agents shall have the right to enter the Property at any time, with or without notice…",
      "explanation": "This violates California Civil Code 1954, which requires 24-hour notice except for emergencies.",
      "suggestion": "Replace with California-compliant language requiring 24-hour notice except for emergencies."
    },
    "..."
  ],
  "warnings": [
    {
      "title": "High early termination penalty",
      "severity": "yellow",
      "clause": "Section 1",
      "quote": "Early termination by Tenant shall result in a penalty equal to three (3) months' rent.",
      "explanation": "A 3-month penalty ($9,600) is quite steep and may exceed actual damages to landlord from early termination.",
      "suggestion": "Negotiate for lower penalty (1-2 months) or ability to mitigate by helping find replacement tenant."
    },
    "..."
  ],
  "good_clauses": [
    {
      "title": "Clear rent amount and due date",
      "clause": "Section 2",
      "explanation": "The lease clearly states the monthly rent ($3,200) and due date (1st of each month)."
    },
    {
      "title": "Defined lease term",
      "clause": "Section 1",
      "explanation": "The lease has a clear start and end date, providing certainty about the rental period."
    }
  ],
  "missing_protections": [
    "Habitability warranty from landlord",
    "Tenant's right to make necessary repairs and deduct from rent",
    "Protection against retaliatory eviction",
    "..."
  ],
  "fairness_score": 15,
  "fairness_grade": "F"
}
```

### PDF / DOCX contracts

This example accepts the contract as `text` only. To analyse a PDF or DOCX,
pre-extract the text on the client side and send it as a text part —
ContractGuard's own parser is the cleanest tool for the job:

```python
from contractguard.parser import extract_text
contract_text = extract_text("my-lease.pdf")
# … then send contract_text as the `text` value of a text part
```

Bindu does ship a native file-extraction interceptor, but it does not
round-trip cleanly with the current A2A `FilePart` wire shape in this
version. Pre-extracting client-side is the reliable path until that's fixed
upstream.

### Response shape

The result artifact's text part contains the existing
[`AnalysisResult`](../../contractguard/models.py) serialised to JSON. The
full structure — `contract_type`, `summary`, `parties`, `key_terms`,
`red_flags[]`, `warnings[]`, `good_clauses[]`, `missing_protections[]`,
`fairness_score`, `fairness_grade` — is unchanged from the CLI's `--json`
output, so any code that already consumes `contractguard scan --json` works
without modification. The artifact part carries a `did.message.signature`
in its metadata: Ed25519 over the result, verifiable against the public key
in `/.well-known/did.json`.

If the analyser raises (no API key, model error, schema mismatch), the
result is wrapped in a structured error instead:

```json
{ "error": "analysis_failed", "message": "Error code: 401 - …" }
```

## Charging per scan (x402)

[x402](https://www.x402.org/) is an open micropayment protocol — Bindu
speaks it natively. Uncomment the `execution_cost` block in
[`agent.py`](agent.py) and fill in your wallet:

```python
"execution_cost": {
    "amount": "0.10",
    "token": "USDC",
    "network": "base-sepolia",
    "pay_to_address": "0xYOUR_ADDRESS_HERE",
},
```

The agent now responds with HTTP 402 to unauthenticated calls; the caller
attaches a USDC payment proof and the agent verifies + analyses. This is
the shortest path from "open-source CLI" to "monetised hosted service"
without adding a SaaS layer.

## Limits and notes

- **Not legal advice.** Same caveat as the upstream CLI — this is a
  first-pass filter, not a lawyer.
- **Contract length.** Inputs >120k chars are truncated (see
  `MAX_CONTRACT_CHARS` in `contractguard.analyzer`). For 60+ page
  contracts, pick a long-context model via
  `CONTRACTGUARD_MODEL=google/gemini-2.5-pro`.
- **Streaming** isn't enabled — analyses come back as a single artifact.
- **Auth defaults are off.** Suitable for localhost / trusted networks. For
  a public deployment set `AUTH__ENABLED=true` and follow Bindu's
  [`AUTH.md`](https://github.com/getbindu/Bindu/blob/main/docs/AUTH.md).
