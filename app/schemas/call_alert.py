from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# =====================================================================
# METADATA SUB-SCHEMAS (Used for Parsing)
# =====================================================================
class WhatsAppCallWebhookItem(BaseModel):
    """
    Validates individual call event items inside Meta's changes array array.
    """
    id: str
    to: str
    from_field: str = Field(..., alias="from")  # Maps 'from' without breaking Python keywords
    timestamp: int
    event: str

    class Config:
        populate_by_name = True

# =====================================================================
# DATABASE STORAGE CONTRACT (Next.js Dashboard Consumption)
# =====================================================================
class CallDatabaseSchema(BaseModel):
    """
    The rigid layout schema saved directly into your MongoDB 'calls' collection.
    The Next.js team relies directly on this document layer.
    """
    call_id: str
    caller_phone: str
    wa_id: str
    name: str = "Unknown"
    call_event: str
    date_time: datetime