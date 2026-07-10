from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import ChatRequest, ChatResponse, JobApproveRequest
from . import router as intent_router
from .mocks import ansible_mock, helix_mock

app = FastAPI(title="ITSM AI Assistant - Local POC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # POC only -- restrict this in any non-local deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "mode": "local-poc"}


@app.post("/api/chat")
def chat(req: ChatRequest):
    result = intent_router.handle_message(req.message, req.user)
    return result


@app.post("/api/jobs/approve")
def approve_job(req: JobApproveRequest):
    result = intent_router.approve_job(
        req.job_template, req.target, req.requested_by, req.ticket_id
    )
    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    return result


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    status = ansible_mock.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="job not found")
    return status


@app.get("/api/audit-log")
def audit_log():
    return helix_mock.get_audit_log()
