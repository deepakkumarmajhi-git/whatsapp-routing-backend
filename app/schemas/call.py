from pydantic import BaseModel, Field
from datetime import datetime

# =====================================================================
# INBOUND WEBHOOK PAYLOAD SUB-SCHEMA
# =====================================================================
class WhatsAppCallWebhookItem(BaseModel):
    """Validates individual call items inside Meta's payload."""
    id: str
    to: str
    from_field: str = Field(..., alias="from")  # Maps 'from' safely
    timestamp: int
    event: str

    class Config:
        populate_by_name = True

# =====================================================================
# DATABASE STORAGE CONTRACT (Next.js Dashboard Consumption)
# =====================================================================
class CallDatabaseSchema(BaseModel):
    """The rigid layout schema saved into your MongoDB 'calls' collection."""
    call_id: str
    caller_phone: str
    wa_id: str
    name: str = "Unknown"
    call_event: str
    date_time: datetime