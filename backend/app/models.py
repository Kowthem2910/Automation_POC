from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    message: str
    user: str = "jordan.s"


class ChatResponse(BaseModel):
    intent: str
    reply_text: Optional[str] = None
    card_type: Optional[str] = None   # "ticket" | "kb" | "job" | "alert" | None
    card_data: Optional[Dict[str, Any]] = None
    followups: Optional[List[Dict[str, Any]]] = None


class JobApproveRequest(BaseModel):
    job_template: str
    target: str
    requested_by: str = "jordan.s"
    ticket_id: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # queued | running | success | failed
    steps_completed: List[str]
    total_steps: int
    result_summary: Optional[str] = None
