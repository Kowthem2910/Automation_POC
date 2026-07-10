# POC Flow — What's Real vs. Mocked

This document maps every component in the running POC to what it actually
does today, so it's clear what's demonstrated logic vs. what's a stand-in
for a system this POC doesn't have live access to yet.

## Summary table

| Component | In this POC | In production |
|---|---|---|
| Chat UI | Teams-styled static HTML, calls the real backend over `fetch` | Real Microsoft Teams client via Azure Bot Service |
| Intent routing | Real code — `router.py` classifies and dispatches every message | Same code, unchanged |
| Intent classification | Real Claude API call if `ANTHROPIC_API_KEY` is set; rule-based fallback otherwise | Real Claude API call, always |
| Incident categorization/priority | Real Claude API call if key set; keyword fallback otherwise | Real Claude API call, always |
| Knowledge base search (RAG) | Real TF-IDF retrieval over 3 local Markdown KB articles | Real embeddings + vector DB (OpenSearch/pgvector) over the full live Helix KB, kept in sync via ingestion pipeline |
| Ticket data (Helix) | Mocked — 2 fixture tickets + create/read logic, backed by a real SQLite audit log | Real Helix REST API calls |
| CMDB data (NetBox) | Mocked — 2 fixture CI records | Real NetBox REST API calls |
| Monitoring alerts (Zabbix) | Mocked — 1 fixture active alert | Real Zabbix JSON-RPC API calls |
| Remediation (Ansible) | Mocked — simulated async job with real threading/polling behavior, real whitelist enforcement logic | Real AWX API (`launch` + poll/webhook), same whitelist enforcement logic |
| Audit trail | Real — every bot action is written to a local SQLite file (`audit_log.db`) | Real — written to Helix as ticket work notes / audit records |
| Approval gate | Present (Approve/Deny buttons), but no real permission check | Same UI pattern, backed by a real role/permission check against Entra ID or Helix's approval matrix |

## What this means

**Real and reusable as-is:**
- The orchestration logic in `router.py` — classify, dispatch, enrich, respond
- The whitelist-enforcement pattern in `ansible_mock.py` (`is_whitelisted()`) —
  this exact server-side check is the safety boundary in production too
- The async job launch/poll pattern — mirrors AWX's real `launch` + status
  polling API shape exactly, just faster
- The audit-log-on-every-action pattern
- The RAG retrieval pattern: chunk → score → threshold → ground-or-fallback

**Needs real design work before production:**
- Swapping fixture data for live API clients (Helix/NetBox/Zabbix/AWX) —
  mostly a matter of writing HTTP client modules with the same function
  signatures as the mocks
- A real permission check on the approval gate
- A real KB ingestion pipeline (see `diagrams/rag-ingestion-pipeline.mermaid`)
  instead of static files loaded once at startup
- Moving from local dev to the Teams channel + AWS hosting shell (see
  `diagrams/production-architecture.mermaid`)

## Running the POC

```bash
cd backend
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...   # optional — omit to use rule-based fallback
uvicorn app.main:app --reload
```

Then open `frontend/index.html` in a browser (backend must be running on
`localhost:8000` — CORS is wide open for local dev only).

Try the four quick-action chips, or type your own message. Every response
is generated live by the backend, not scripted.
