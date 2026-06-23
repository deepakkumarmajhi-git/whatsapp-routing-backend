from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==========================================
# 1. API Requests (Next.js -> FastAPI)
# ==========================================
class TaskAssignRequest(BaseModel):
    """Payload the frontend sends when Manager assigns a task to a worker."""
    task_id: str = Field(..., description="The internal MongoDB ID of the task")
    worker_phone: str = Field(..., description="The WhatsApp number of the assigned worker")

class WorkerTemplateRequest(BaseModel):
    """Payload for triggering the Meta template to the worker."""
    recipient_phone: str
    template_name: str = "task_assignment_alert"

# ==========================================
# 2. API Responses (FastAPI -> Next.js)
# ==========================================
class TaskResponse(BaseModel):
    """How a task object looks when the frontend fetches it for the dashboard."""
    id: str = Field(..., alias="_id")
    customer_phone: str
    status: str  # "pending", "assigned", "completed"
    last_message: str
    priority: str = "normal"  # Highlights "high" priority items like Missed Calls
    assigned_worker: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class StandardResponse(BaseModel):
    """A generic success wrapper for UI toast notifications."""
    status: str
    message: str