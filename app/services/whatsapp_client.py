import httpx
from fastapi import HTTPException
from app.config.config import settings
from app.schemas.tasks import WorkerTemplateRequest

class WhatsAppClient:
    def __init__(self):
        # We construct the official Meta Graph API URL dynamically
        self.base_url = f"https://graph.facebook.com/{settings.META_API_VERSION}/{settings.PHONE_NUMBER_ID}/messages"
        self.headers = {
            "Authorization": f"Bearer {settings.META_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

    async def send_template_message(self, payload: WorkerTemplateRequest):
        """Dispatches a pre-approved Meta template (e.g., for task assignment)."""
        meta_payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": payload.recipient_phone,
            "type": "template",
            "template": {
                "name": payload.template_name,
                "language": {"code": "en_US"}
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.base_url, json=meta_payload, headers=self.headers)
            if response.status_code not in [200, 201]:
                print(f"❌ Meta API Error: {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to send Meta template")
            return response.json()

    async def send_text_message(self, recipient_phone: str, message_body: str):
        """Dispatches a standard text message (only works inside the 24-hour window)."""
        meta_payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {"body": message_body}
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.base_url, json=meta_payload, headers=self.headers)
            if response.status_code not in [200, 201]:
                raise HTTPException(status_code=response.status_code, detail="Failed to send Meta text")
            return response.json()

# Instantiate it so you can import 'whatsapp_service' anywhere in your app
whatsapp_service = WhatsAppClient()