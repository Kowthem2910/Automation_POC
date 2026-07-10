# Real Flow — Production Target Architecture

This describes the architecture this POC is built to grow into. See
`diagrams/production-architecture.mermaid` for the full diagram; this
document walks through it in words.

## Phase 1 — Local pilot (this repo)
Backend and RAG logic run locally against mock ITSM/infra APIs. Proves out
the AI orchestration, RAG grounding, and remediation-approval pattern
without depending on network access to real Helix/NetBox/Zabbix/AWX or on
Teams/Azure Bot Service approval.

See `docs/POC_FLOW.md` and `diagrams/local-poc-architecture.mermaid`.

## Phase 2 — AWS migration
Once the local POC is validated:
- Containerize the backend (`Dockerfile` to be added) → deploy to ECS
  Fargate behind an ALB
- Replace the local vector store (`rag.py`'s TF-IDF matrix) with
  OpenSearch or pgvector on RDS
- Move secrets (Helix/NetBox/Zabbix/AWX API keys) to AWS Secrets Manager
- Optionally swap the Claude API call for Amazon Bedrock if LLM traffic
  needs to stay inside the VPC

## Phase 3 — Teams production rollout
- Register the bot in Azure Bot Service via the org's Teams tenant
- Repoint the messaging endpoint to the AWS-hosted backend
- No backend logic changes required — only the channel/front-end layer
  changes; `router.py` and everything below it stays the same

## Live-setup behavior differences from the POC

Two components behave meaningfully differently once wired to real
systems — see the dedicated diagrams for each:

- **RAG / knowledge base** — becomes an ongoing ingestion pipeline
  (webhook or scheduled sync from Helix, chunking, metadata tagging,
  re-embedding) rather than a one-time load of static files. See
  `diagrams/rag-ingestion-pipeline.mermaid`.
- **Ansible remediation** — becomes a real async integration with AWX:
  launch a job template, then poll or receive a completion webhook,
  handle real failures, and cross-link the Helix ticket with the AWX job
  run. See `diagrams/ansible-async-job-flow.mermaid`.

## Design decisions still open

- **RAG sync method** — webhook (near real-time, needs Helix to support
  outbound webhooks on article publish) vs. scheduled poll (simpler to
  build, hours of staleness)
- **AWX completion method** — polling (simpler, more API load) vs.
  notification webhook (more efficient, needs AWX admin to enable
  outbound webhooks to the backend)
- **Approval permission model** — who can approve a remediation action?
  Needs to be tied to a real role/group source (Entra ID group membership
  or Helix's own approval matrix), not left open to anyone in the chat
