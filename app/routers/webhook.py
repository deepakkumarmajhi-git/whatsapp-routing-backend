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
    """Receives WhatsApp webhooks and isolates messages and calls securely into MongoDB."""
    messages_collection = get_collection("messages")
    tasks_collection = get_collection("tasks")
    calls_collection = get_collection("calls")  # Target collection for all voice/video events
    
    try:
        payload = await request.json()
        entries = payload.get("entry", [])

        for entry in entries:
            for change in entry.get("changes", []):
                field = change.get("field")
                value = change.get("value", {})
                contacts = value.get("contacts", [])

                # 1. Build a fast contact mapper dictionary
                contact_map = {}
                wa_id = None
                name = "Unknown"
                
                for contact in contacts:
                    c_wa_id = contact.get("wa_id")
                    c_name = contact.get("profile", {}).get("name", "Unknown")
                    if c_wa_id:
                        contact_map[c_wa_id] = c_name
                        wa_id = c_wa_id  # Keeps track of the active iteration variables
                        name = c_name

                # -------------------------------------------------------------
                # SCENARIO A: Process Incoming Call Tracking Fields
                # -------------------------------------------------------------
                if field == "calls" or "calls" in value:
                    for call in value.get("calls", []):
                        call_id = call.get("id")
                        caller_phone = call.get("from")
                        call_event = call.get("event")
                        raw_timestamp = call.get("timestamp")
                        
                        # Convert epoch integer to a standard UTC datetime object
                        date_time = datetime.fromtimestamp(int(raw_timestamp)) if raw_timestamp else datetime.utcnow()
                        
                        # Extract their correct profile name using the contact metadata map
                        caller_name = contact_map.get(caller_phone, "Unknown")
                        caller_wa_id = caller_phone  # Meta's call 'from' acts as their WhatsApp identifier
                        
                        # Insert standard clean contract for the dashboard into 'calls' collection
                        await calls_collection.insert_one({
                            "call_id": call_id,
                            "caller_phone": caller_phone,
                            "wa_id": caller_wa_id,
                            "name": caller_name,
                            "call_event": call_event,
                            "date_time": date_time
                        })
                        print(f"🚨 Stored {call_event} call history log for {caller_name} ({caller_phone})")
                        
                        # --- TODO: Real-time WebSocket trigger for the Call Dashboard goes here! ---

                # -------------------------------------------------------------
                # SCENARIO B: Process Standard Core Chat Threads
                # -------------------------------------------------------------
                elif field == "messages":
                    for msg in value.get("messages", []):
                        msg_id = msg.get("id")
                        sender = msg.get("from")
                        body = msg.get("text", {}).get("body", "[Non-text payload]")
                        
                        # 1. Save the raw chat log to MongoDB
                        await messages_collection.insert_one({
                            "message_id": msg_id,
                            "sender_phone": sender,
                            "wa_id": wa_id,
                            "name": name,
                            "text": body,
                            "timestamp": datetime.utcnow()
                        })
                        
                        # 2. Update or Create an active Dashboard Task
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
                        print(f"✅ Stored message and updated Task for {sender}")
                        
                        # --- TODO: WebSocket Trigger for Chat Dashboard goes here! ---
                        
    except Exception as e:
        print(f"❌ Webhook Processing Error: {e}")
        
    return {"status": "success"}