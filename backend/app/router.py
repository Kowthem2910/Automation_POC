"""
Intent router -- the orchestration core.

This is the one piece of the whole POC that is NOT a mock: the routing
logic here (classify -> dispatch -> enrich -> respond) is exactly the
shape production code would take. Only the things it calls out to
(helix_mock, zabbix_mock, netbox_mock, ansible_mock) get swapped for real
API clients later.
"""

import re
from . import llm, rag
from .mocks import helix_mock, zabbix_mock, netbox_mock, ansible_mock


def _extract_ticket_id(message: str):
    match = re.search(r"INC\d{7}", message.upper())
    return match.group(0) if match else None


def handle_message(message: str, user: str) -> dict:
    intent = llm.classify_intent(message)

    if intent == "ticket_status":
        ticket_id = _extract_ticket_id(message) or "INC0012345"  # demo default
        ticket = helix_mock.get_ticket(ticket_id)
        if not ticket:
            return {
                "intent": intent,
                "reply_text": f"I couldn't find a ticket matching {ticket_id}.",
            }
        related_alerts = zabbix_mock.get_active_alerts(ticket["category"].split(">")[-1].strip())
        helix_mock.write_audit(user, "ticket_status_checked", ticket_id)
        return {
            "intent": intent,
            "card_type": "ticket",
            "card_data": ticket,
            "reply_text": f"Here's the current status of {ticket_id}.",
            "followups": [{"type": "alert", "data": related_alerts[0]}] if related_alerts else None,
        }

    if intent == "kb_question":
        results = rag.search_kb(message, top_k=1)
        helix_mock.write_audit(user, "kb_search", message)
        if not results:
            return {
                "intent": intent,
                "reply_text": (
                    "I couldn't find a knowledge base article that matches that. "
                    "Would you like me to log a ticket instead?"
                ),
            }
        return {
            "intent": intent,
            "card_type": "kb",
            "card_data": results[0],
            "reply_text": "Here's what I found in the knowledge base.",
        }

    if intent == "create_incident":
        # check for an existing related active alert / ticket first (dedup pattern)
        alerts = zabbix_mock.get_active_alerts()
        for alert in alerts:
            if any(w in message.lower() for w in ["vpn", "gateway", "network"]):
                helix_mock.write_audit(user, "incident_linked_not_duplicated", "INC0012345")
                ticket = helix_mock.get_ticket("INC0012345")
                return {
                    "intent": intent,
                    "card_type": "ticket",
                    "card_data": ticket,
                    "reply_text": (
                        "I found an existing related incident already in progress, "
                        "so I've linked your report to it instead of opening a duplicate."
                    ),
                    "followups": [{"type": "alert", "data": alert}],
                }

        classification = llm.categorize_incident(message)
        ticket = helix_mock.create_ticket(
            summary=message,
            category=classification["category"],
            priority=classification["priority"],
            opened_by=user,
        )
        return {
            "intent": intent,
            "card_type": "ticket",
            "card_data": ticket,
            "reply_text": f"I've logged a new incident: {ticket['id']}.",
        }

    if intent == "run_remediation":
        target = "web01.prod.internal" if "apache" in message.lower() or "web01" in message.lower() else None
        job_template = "restart-apache-service" if target else None
        if not job_template:
            return {
                "intent": intent,
                "reply_text": "I don't have an approved automation matching that request.",
            }
        ci = netbox_mock.get_ci(target)
        return {
            "intent": intent,
            "card_type": "job_confirm",
            "card_data": {
                "job_template": job_template,
                "target": target,
                "risk": ansible_mock.JOB_TEMPLATES[job_template]["risk"],
                "ci_owner": ci["owner"] if ci else "Unknown",
            },
            "reply_text": "This action requires your approval before it runs.",
        }

    return {
        "intent": "unknown",
        "reply_text": (
            "I can help with: checking a ticket status, logging an incident, "
            "searching the knowledge base, or running an approved fix."
        ),
    }


def approve_job(job_template: str, target: str, user: str, ticket_id: str = None) -> dict:
    if not ansible_mock.is_whitelisted(job_template, target):
        helix_mock.write_audit(user, "remediation_denied_not_whitelisted", f"{job_template} on {target}")
        return {"error": "not_whitelisted"}
    job_id = ansible_mock.launch_job(job_template, target)
    helix_mock.write_audit(user, "remediation_approved", f"{job_template} on {target} (job {job_id})")
    return {"job_id": job_id}
