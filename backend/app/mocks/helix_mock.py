"""
Mock Helix ITSM API.

REAL FLOW NOTE:
In production this module is replaced by real HTTP calls to the Helix REST
API (ticket CRUD, KB article fetch, audit log write). The function
signatures below intentionally mirror what those real client calls would
look like, so swapping this module for a `helix_client.py` that calls
requests.get/post against the real Helix instance is a drop-in replacement
-- the router and rest of the app don't need to change.
"""

import sqlite3
import time
import uuid
from pathlib import Path

DB_PATH = Path(__file__).parent / "audit_log.db"

# --- Mock ticket store (in production: GET /api/arsys/v1/entry/HPD:Help Desk) ---
TICKETS = {
    "INC0012345": {
        "id": "INC0012345",
        "status": "In Progress",
        "priority": "P2",
        "assignee": "Network Ops - T. Alvarez",
        "opened": "2026-07-09 08:12",
        "summary": "VPN gateway intermittent drops - East DC",
        "category": "Network > VPN",
    },
    "INC0012298": {
        "id": "INC0012298",
        "status": "Resolved",
        "priority": "P4",
        "assignee": "Service Desk - Auto",
        "opened": "2026-07-07 14:02",
        "summary": "Password reset request",
        "category": "Access > Password",
    },
}


def _init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY,
            ts REAL,
            actor TEXT,
            action TEXT,
            detail TEXT
        )"""
    )
    conn.commit()
    conn.close()


_init_db()


def get_ticket(ticket_id: str):
    """Mirrors: GET /helix/api/tickets/{id}"""
    return TICKETS.get(ticket_id.upper())


def create_ticket(summary: str, category: str, priority: str, opened_by: str):
    """Mirrors: POST /helix/api/tickets"""
    new_id = f"INC{uuid.uuid4().int % 9000000 + 1000000}"
    TICKETS[new_id] = {
        "id": new_id,
        "status": "New",
        "priority": priority,
        "assignee": "Unassigned - Auto-Triage Queue",
        "opened": time.strftime("%Y-%m-%d %H:%M"),
        "summary": summary,
        "category": category,
    }
    write_audit(opened_by, "ticket_created", f"{new_id}: {summary}")
    return TICKETS[new_id]


def write_audit(actor: str, action: str, detail: str):
    """Mirrors: POST /helix/api/audit  (every bot action is logged here)"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO audit_log VALUES (?,?,?,?,?)",
        (str(uuid.uuid4()), time.time(), actor, action, detail),
    )
    conn.commit()
    conn.close()


def get_audit_log(limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT ts, actor, action, detail FROM audit_log ORDER BY ts DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [
        {"ts": r[0], "actor": r[1], "action": r[2], "detail": r[3]} for r in rows
    ]
