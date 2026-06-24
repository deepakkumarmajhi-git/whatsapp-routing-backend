from fastapi import APIRouter, HTTPException, Query, Response, status, Request
from datetime import datetime
from app.config.config import settings
from app.config.database import get_collection

router = APIRouter(prefix="/webhook", tags=["Meta Webhooks"])

@router.get("")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: int = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """Handles the initial Meta Developer Dashboard verification handshake."""
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        return Response(content=str(hub_challenge), media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@router.post("", status_code=status.HTTP_200_OK)
async def receive_webhook(request: Request):
    """Receives WhatsApp webhooks and stores them directly in MongoDB."""
    messages_collection = get_collection("messages")
    tasks_collection = get_collection("tasks")
    
    try:
        payload = await request.json()
        entries = payload.get("entry", [])

        for entry in entries:
            for change in entry.get("changes", []):
                field = change.get("field")
                value = change.get("value", {})
                contacts = value.get("contacts", [])

                contact_map = {}
                for contact in contacts:
                    wa_id = contact.get("wa_id")
                    name = contact.get("profile", {}).get("name", "Unknown")
                    if wa_id:
                        contact_map[wa_id] = name
                    
                if field == "messages":
                    for msg in value.get("messages", []):
                        sender = msg.get("from")
                        msg_id = msg.get("id")
                        body = msg.get("text", {}).get("body", "[Non-text payload]")
                        customer_name = contact_map.get(sender, "Unknown Contact")
                        
                        # 1. Save the raw chat log to MongoDB
                        await messages_collection.insert_one({
                            "message_id": msg_id,
                            "sender_phone": sender,
                            "wa_id" : sender,
                            "customer_name": customer_name,
                            "text": body,
                            "timestamp": datetime.utcnow()
                        })
                        
                        # 2. Update or Create an active Dashboard Task
                        await tasks_collection.update_one(
                            {"customer_phone": sender, "status": {"$ne": "completed"}},
                            {"$set": {
                                "customer_phone": sender,
                                "wa_id": sender,
                                "customer_name": customer_name,
                                "status": "pending",
                                "last_message": body,
                                "updated_at": datetime.utcnow()
                            }},
                            upsert=True
                        )
                        print(f"✅ Stored message and updated Task for {sender}")
                        
                        # --- TODO: WebSocket Trigger goes here! ---
                        
    except Exception as e:
        print(f"❌ Webhook Processing Error: {e}")
        
    return {"status": "success"}