# ITSM AI Assistant — Local POC

An AI-powered ITSM assistant (Teams-styled chat UI) that handles ticket
status checks, incident creation, knowledge base Q&A (RAG), and approved
Ansible remediations — built as a local proof of concept ahead of a full
Teams + AWS production rollout.

This POC is part of the ITSM/IDL Automation & AI initiative, satisfying:
- 1 AI-enabled POC deliverable
- Demonstrates 2 automation patterns (auto-triage/categorization, approved
  remediation execution)

## Two ways to view this

**`frontend/standalone-demo.html`** — zero setup, open it directly in a
browser. Runs entirely on scripted mock JavaScript, no backend required.
Use this for a quick, guaranteed-to-work visual walkthrough with
stakeholders who just want to see the concept.

**`frontend/index.html`** — the real POC. Calls the actual FastAPI backend
below for every response (real intent routing, real RAG retrieval, real
async job polling). Use this to show that the underlying logic genuinely
works, not just the UI.

## Quick start (real POC)

```bash
cd backend
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...   # optional, see below
uvicorn app.main:app --reload
```

Open `frontend/index.html` in a browser. The backend must be running on
`http://localhost:8000`.

**No API key?** The backend still runs end-to-end using rule-based intent
classification and categorization instead of live Claude API calls — see
`backend/app/llm.py`.

## Try it

Click a quick-action chip, or type your own message:
- `check status INC0012345` — pulls a mock Helix ticket + cross-references
  an active mock Zabbix alert
- `my vpn client won't connect` — detects the related active incident and
  links to it instead of creating a duplicate
- `how do I reset my vpn client` — real TF-IDF retrieval over local KB
  fixtures (RAG pattern)
- `restart apache on web01` — shows an approval card; approving launches a
  simulated async Ansible job with real polling behavior, logged to a
  local SQLite audit trail

## Repo structure

```
backend/
  app/
    main.py          FastAPI app + routes
    router.py         Intent routing / orchestration (the reusable core)
    llm.py             Claude API wrapper + rule-based fallback
    rag.py              TF-IDF KB retrieval
    models.py            Pydantic request/response models
    kb_data/               Sample KB articles (Markdown + frontmatter)
    mocks/
      helix_mock.py         Mock ticket store + real SQLite audit log
      netbox_mock.py          Mock CMDB/CI data
      zabbix_mock.py            Mock active alerts
      ansible_mock.py            Mock AWX job launch/poll simulation
  requirements.txt
frontend/
  index.html          Teams-styled chat UI, calls the live backend
docs/
  POC_FLOW.md          What's real vs. mocked in this POC
  REAL_FLOW.md           Production target architecture (Phases 1-3)
diagrams/
  local-poc-architecture.mermaid    This POC's architecture
  production-architecture.mermaid     Full Teams + AWS target architecture
  rag-ingestion-pipeline.mermaid        Live KB ingestion flow
  ansible-async-job-flow.mermaid          Live AWX job execution flow
```

## What's real vs. mocked

See [`docs/POC_FLOW.md`](docs/POC_FLOW.md) for the full breakdown. Short
version: the orchestration logic, RAG retrieval, whitelist enforcement,
async job pattern, and audit logging are all real. Helix/NetBox/Zabbix/AWX
are fixture data standing in for the real APIs, so this POC has zero
external dependencies beyond the Claude API (optional).

## Where this goes next

See [`docs/REAL_FLOW.md`](docs/REAL_FLOW.md) for the Phase 2 (AWS) and
Phase 3 (Teams production) migration path, and how RAG and Ansible
remediation behave differently once wired to live systems.
