from pydantic import BaseModel, Field
from typing import List, Optional, Any

# ==========================================
# 1. Standard Messaging Entities
# ==========================================
class TextMessage(BaseModel):
    body: Optional[str] = None

class MessageContext(BaseModel):
    from_: Optional[str] = Field(None, alias="from")
    id: Optional[str] = None

class Message(BaseModel):
    id: str
    from_: str = Field(..., alias="from")
    timestamp: str
    type: str
    text: Optional[TextMessage] = None
    context: Optional[MessageContext] = None

# ==========================================
# 2. Resilient Group Tracking Entities
# ==========================================
class ParticipantItem(BaseModel):
    wa_id: Optional[str] = None
    input: Optional[str] = None

class TextUpdate(BaseModel):
    text: Optional[str] = None
    update_successful: Optional[bool] = None

class GroupEvent(BaseModel):
    timestamp: str
    group_id: str
    type: str  # e.g., group_create, group_participants_add
    subject: Optional[str] = None
    invite_link: Optional[str] = None
    added_participants: Optional[List[ParticipantItem]] = None
    removed_participants: Optional[List[ParticipantItem]] = None
    group_subject: Optional[TextUpdate] = None

class GroupStatusItem(BaseModel):
    id: str
    status: str
    timestamp: str
    recipient_id: str  
    recipient_type: str  
    recipient_participant_id: Optional[str] = None  

# ==========================================
# 3. Top-Level Core Payload Wrappers
# ==========================================
class Value(BaseModel):
    messaging_product: str
    messages: Optional[List[Message]] = None
    statuses: Optional[List[GroupStatusItem]] = None  
    groups: Optional[List[GroupEvent]] = None  

class Change(BaseModel):
    field: str  
    value: Value

class Entry(BaseModel):
    id: str
    changes: List[Change]

class WhatsAppWebhookPayload(BaseModel):
    object: str
    entry: List[Entry]