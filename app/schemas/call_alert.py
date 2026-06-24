from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# ==========================================
# 1. DATABASE STORAGE SCHEMA (Next.js Dashboard Contract)
# ==========================================
class CallDatabaseSchema(BaseModel):
    """
    This defines the exact structure of the document stored in your MongoDB 'calls' collection.
    Your Next.js frontend team will consume this exact payload structure.
    """
    call_id: str
    caller_phone: str
    wa_id: str
    name: str = "Unknown"
    call_event: str
    date_time: datetime

# ==========================================
# 2. INBOUND WEBHOOK PAYLOAD SUB-SCHEMA
# ==========================================
class WhatsAppCallWebhookItem(BaseModel):
    """
    Validates individual call entries inside Meta's webhook changes array.
    """
    id: str
    to: str
    from_field: str = Field(..., alias="from")  # Correctly aliases Meta's reserved keyword 'from'
    timestamp: int
    event: str

    class Config:
        populate_by_name = True