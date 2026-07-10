"""
Mock Ansible AWX integration.

REAL FLOW NOTE:
Production calls AWX's REST API:
  1. POST /api/v2/job_templates/{id}/launch/   -> returns {"job": <job_id>}
  2. GET  /api/v2/jobs/{job_id}/                -> poll until status is
     "successful" / "failed" / "error"  (or receive a notification webhook
     on completion instead of polling)

This mock reproduces that exact two-call shape (launch, then poll) using a
background thread that advances an in-memory job through a step list over
a few seconds, so the frontend's polling loop behaves the same way it
would against a real AWX instance -- just faster.

WHITELIST NOTE: only job templates listed in JOB_TEMPLATES may be launched.
The router must never accept an arbitrary playbook name from the LLM or
the user -- this whitelist is the actual safety boundary, enforced here
server-side, not by the LLM's judgment.
"""

import threading
import time
import uuid

JOB_TEMPLATES = {
    "restart-apache-service": {
        "risk": "Low (whitelisted)",
        "steps": [
            "Connecting to target host",
            "Checking service health",
            "Restarting apache2",
            "Verifying HTTP 200 response",
            "Writing result to audit trail",
        ],
        "allowed_targets": ["web01.prod.internal"],
    },
    "reset-password": {
        "risk": "Low (whitelisted)",
        "steps": [
            "Validating requester identity",
            "Generating temporary credential",
            "Applying to directory service",
            "Notifying user",
        ],
        "allowed_targets": ["*"],
    },
}

_JOBS = {}  # job_id -> job state dict
_LOCK = threading.Lock()


def is_whitelisted(job_template: str, target: str) -> bool:
    tpl = JOB_TEMPLATES.get(job_template)
    if not tpl:
        return False
    if tpl["allowed_targets"] == ["*"]:
        return True
    return target in tpl["allowed_targets"]


def launch_job(job_template: str, target: str) -> str:
    """Mirrors: POST /awx/api/v2/job_templates/{id}/launch/"""
    tpl = JOB_TEMPLATES[job_template]
    job_id = str(uuid.uuid4())[:8]
    with _LOCK:
        _JOBS[job_id] = {
            "job_id": job_id,
            "job_template": job_template,
            "target": target,
            "status": "queued",
            "steps_completed": [],
            "total_steps": len(tpl["steps"]),
            "result_summary": None,
        }
    threading.Thread(target=_run_job, args=(job_id, tpl["steps"]), daemon=True).start()
    return job_id


def _run_job(job_id: str, steps: list):
    with _LOCK:
        _JOBS[job_id]["status"] = "running"
    for step in steps:
        time.sleep(1.0)  # simulate real execution latency
        with _LOCK:
            _JOBS[job_id]["steps_completed"].append(step)
    with _LOCK:
        _JOBS[job_id]["status"] = "success"
        _JOBS[job_id]["result_summary"] = (
            f"{_JOBS[job_id]['job_template']} completed successfully on "
            f"{_JOBS[job_id]['target']}."
        )


def get_job_status(job_id: str):
    """Mirrors: GET /awx/api/v2/jobs/{job_id}/"""
    with _LOCK:
        return _JOBS.get(job_id)
