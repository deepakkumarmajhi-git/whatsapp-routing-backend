from fastapi import APIRouter, HTTPException, Query, Response, status
from datetime import datetime
from app.config.config import settings
from app.config.database import get_collection
from app.schemas.webhooks import MetaWebhookPayload

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
async def receive_webhook(payload: MetaWebhookPayload):
    """Receives strongly-typed WhatsApp webhooks from Meta."""
    messages_collection = get_collection("messages")
    tasks_collection = get_collection("tasks")
    calls_collection = get_collection("calls")
    
    try:
        for entry in payload.entry:
            for change in entry.changes:
                field = change.field
                value = change.value
                
                # 1. Build a fast contact mapper dictionary
                contact_map = {}
                wa_id = None
                name = "Unknown"
                
                for contact in value.contacts:
                    c_wa_id = contact.wa_id
                    c_name = contact.profile.name
                    if c_wa_id:
                        contact_map[c_wa_id] = c_name
                        wa_id = c_wa_id  
                        name = c_name

                # -------------------------------------------------------------
                # SCENARIO A: Process Incoming Call Tracking Logs
                # -------------------------------------------------------------
                if field == "calls" or value.calls:
                    calls_list = value.calls or []
                    for call in calls_list:
                        call_id = call.id
                        caller_phone = call.from_field
                        call_event = call.event
                        raw_timestamp = call.timestamp
                        
                        # Convert epoch integer to standard UTC datetime
                        date_time = datetime.fromtimestamp(int(raw_timestamp)) if raw_timestamp else datetime.utcnow()
                        caller_name = contact_map.get(caller_phone, "Unknown")
                        
                        await calls_collection.insert_one({
                            "call_id": call_id,
                            "caller_phone": caller_phone,
                            "wa_id": caller_phone,  # Matches Meta's exact phone ID strings
                            "name": caller_name,
                            "call_event": call_event,
                            "date_time": date_time
                        })
                        print(f"🚨 Call Log Created: {caller_name} ({caller_phone}) -> State: {call_event}")

                # -------------------------------------------------------------
                # SCENARIO B: Process Core Chat Message Flows
                # -------------------------------------------------------------
                elif field == "messages" and value.messages:
                    for msg in value.messages:
                        msg_id = msg.id
                        sender = msg.from_field
                        body = msg.text.body if msg.text else "[Non-text payload]"
                        
                        # Save the raw chat log to MongoDB
                        await messages_collection.insert_one({
                            "message_id": msg_id,
                            "sender_phone": sender,
                            "wa_id": wa_id,
                            "name": name,
                            "text": body,
                            "timestamp": datetime.utcnow()
                        })
                        
                        # Update or Create an active Dashboard Task
                        await tasks_collection.update_one(
                            {"customer_phone": sender, "status": {"$ne": "completed"}},
                            {"$set": {
                                "customer_phone": sender,
                                "wa_id": wa_id,
                                "name": name,
                                "status": "pending",
                                "last_message": body,
                                "updated_at": datetime.utcnow()
                            }},
                            upsert=True
                        )
                        print(f"✅ Message Processed: Task entry synchronized for {sender}")
                        
    except Exception as e:
        print(f"❌ Webhook Processing Error: {e}")
        
    return {"status": "success"}