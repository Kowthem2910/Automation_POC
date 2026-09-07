"""
LLM wrapper. (tested with Claude 4.6)

REAL FLOW NOTE:
If ANTHROPIC_API_KEY is set in the environment, this module calls the real
Claude API to (a) classify intent and (b) categorize/prioritize new
incidents from free text. If no key is set, it falls back to simple
keyword rules so the whole POC still runs end-to-end with zero external
dependencies -- useful for a first demo before API access is wired up.

This is the ONLY component in the POC that makes an outbound network call.
Everything else (Helix/NetBox/Zabbix/Ansible) is local mock data.
"""

import os
import json

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

_client = None
if ANTHROPIC_API_KEY:
    try:
        import anthropic
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    except ImportError:
        _client = None


INTENTS = ["ticket_status", "create_incident", "kb_question", "run_remediation", "unknown"]


def classify_intent(message: str) -> str:
    """Returns one of INTENTS."""
    if _client:
        try:
            resp = _client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=20,
                messages=[{
                    "role": "user",
                    "content": (
                        "Classify this IT support chat message into exactly one label: "
                        "ticket_status, create_incident, kb_question, run_remediation, or unknown. "
                        f"Message: \"{message}\"\nRespond with only the label."
                    ),
                }],
            )
            label = resp.content[0].text.strip().lower()
            if label in INTENTS:
                return label
        except Exception:
            pass  # fall through to rule-based

    lower = message.lower()
    if "status" in lower or lower.strip().upper().startswith("INC"):
        return "ticket_status"
    if "restart" in lower or "remediat" in lower or "run" in lower and "playbook" in lower:
        return "run_remediation"
    if "how do i" in lower or "how to" in lower or "reset my" in lower:
        return "kb_question"
    if "won't connect" in lower or "not working" in lower or "broken" in lower or "issue" in lower or "vpn" in lower:
        return "create_incident"
    return "unknown"


def categorize_incident(message: str) -> dict:
    """Returns {category, priority} for a freeform incident description."""
    if _client:
        try:
            resp = _client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": (
                        "Given this IT incident description, respond ONLY with JSON: "
                        '{"category": "<Area > Subarea>", "priority": "P1|P2|P3|P4"}. '
                        f"Description: \"{message}\""
                    ),
                }],
            )
            text = resp.content[0].text.strip()
            text = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)
            if "category" in data and "priority" in data:
                return data
        except Exception:
            pass

    lower = message.lower()
    if "vpn" in lower:
        return {"category": "Network > VPN", "priority": "P2"}
    if "password" in lower:
        return {"category": "Access > Password", "priority": "P3"}
    return {"category": "General > Unclassified", "priority": "P3"}
