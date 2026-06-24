from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.call import WhatsAppCallWebhookItem

# --- MESSAGES SUB-SCHEMAS ---
class MessageText(BaseModel):
    body: str = "[Non-text payload]"

class WhatsAppMessageItem(BaseModel):
    id: str
    text: Optional[MessageText] = Field(default_factory=MessageText)
    from_field: str = Field(..., alias="from")
    
    class Config:
        populate_by_name = True

# --- SHARED METADATA SUB-SCHEMAS ---
class Profile(BaseModel):
    name: str = "Unknown"

class Contact(BaseModel):
    profile: Profile = Field(default_factory=Profile)
    wa_id: str

class Metadata(BaseModel):
    display_phone_number: Optional[str] = None
    phone_number_id: Optional[str] = None

# --- CORE WEBHOOK PAYLOAD SCHEMAS ---
class WebhookValue(BaseModel):
    messaging_product: str = "whatsapp"
    metadata: Optional[Metadata] = None
    contacts: List[Contact] = Field(default_factory=list)
    messages: Optional[List[WhatsAppMessageItem]] = None
    calls: Optional[List[WhatsAppCallWebhookItem]] = None

class WebhookChange(BaseModel):
    field: str
    value: WebhookValue

class WebhookEntry(BaseModel):
    id: str
    changes: List[WebhookChange]

class MetaWebhookPayload(BaseModel):
    object: str = "whatsapp_business_account"
    entry: List[WebhookEntry]