"""ContractGuard as a Bindu A2A agent.

Wraps `contractguard.analyzer.analyze_contract()` in a Bindu handler so the
analyzer is reachable as a networked, DID-identified microservice over the
A2A JSON-RPC protocol. Peers send the contract as `text` parts in a
`message/send` call and get back the structured `AnalysisResult` (red flags,
warnings, protections, fairness score) as JSON on the result artifact.

For PDF / DOCX inputs, pre-extract on the client with
`contractguard.parser.extract_text()` and send the result as text — see the
README for why.

Run:

    export OPENROUTER_API_KEY=sk-or-...
    pip install -e .
    pip install bindu
    python examples/bindu/agent.py

Agent card:  http://localhost:3773/.well-known/agent.json
DID doc:     http://localhost:3773/.well-known/did.json
JSON-RPC:    POST http://localhost:3773/   (method: message/send)
"""

from __future__ import annotations

import json
import os

from bindu.penguin.bindufy import bindufy

from contractguard.analyzer import DEFAULT_MODEL, analyze_contract


def handler(messages: list[dict]) -> str:
    """A2A handler: pull contract text out of `messages`, analyse, return JSON.

    Bindu normalises A2A messages to `[{"role": "user"|"assistant",
    "content": "..."}]` before calling us. Text parts are concatenated with
    spaces; supported file parts (PDF / DOCX / text/plain) are extracted and
    inlined. We just take everything the user said in this turn and treat it
    as the contract.
    """
    user_content = " ".join(
        (m.get("content") or "") for m in (messages or []) if m.get("role") == "user"
    ).strip()

    if len(user_content) < 50:
        return json.dumps(
            {
                "error": "no_contract",
                "message": (
                    "Send the contract as a `text` part (>= 50 chars) or as a "
                    "`file` part with mimeType pdf, docx, or text/plain."
                ),
            }
        )

    model = os.environ.get("CONTRACTGUARD_MODEL", DEFAULT_MODEL)
    lang = os.environ.get("CONTRACTGUARD_LANG", "en")

    try:
        result = analyze_contract(contract_text=user_content, model=model, lang=lang)
    except Exception as exc:  # noqa: BLE001 — propagate to caller as structured error
        return json.dumps({"error": "analysis_failed", "message": str(exc)})

    return json.dumps(result.model_dump(mode="json"))


config = {
    "author": os.environ.get("CONTRACTGUARD_AUTHOR", "contractguard@example.com"),
    "name": "contractguard",
    "description": (
        "AI contract review agent. Sends a PDF/DOCX/TXT contract or raw text "
        "and returns structured red flags, warnings, protections, and a "
        "fairness score (0-100, A+ to F)."
    ),
    "deployment": {
        "url": "http://localhost:3773",
        "expose": True,
        "cors_origins": ["http://localhost:5173", "http://localhost:3000"],
    },
    # Pay-per-scan via x402 (USDC on Base Sepolia). Uncomment and fill in a
    # pay-to address to charge peers per analysis. Leave commented for free /
    # local development.
    #
    # "execution_cost": {
    #     "amount": "0.10",
    #     "token": "USDC",
    #     "network": "base-sepolia",
    #     "pay_to_address": "0xYOUR_ADDRESS_HERE",
    # },
}


if __name__ == "__main__":
    bindufy(config, handler)
