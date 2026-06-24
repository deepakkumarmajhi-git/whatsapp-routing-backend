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
    """Receives WhatsApp webhooks and handles both Dashboard Test payloads and Live Production payloads."""
    messages_collection = get_collection("messages")
    tasks_collection = get_collection("tasks")
    calls_collection = get_collection("calls")
    
    try:
        payload = await request.json()
        print(f"📩 Received Webhook Payload: {payload}")
        changes_to_process = []

        # ==============================================================
        # 1. CATCH META DASHBOARD TEST PAYLOADS
        # ==============================================================
        if "sample" in payload:
            sample_data = payload.get("sample", {})
            changes_to_process.append({
                "field": sample_data.get("field"),
                "value": sample_data.get("value", {})
            })
            print("🧪 Processing payload from Meta Dashboard Test Tool")

        # ==============================================================
        # 2. CATCH REAL PRODUCTION PAYLOADS
        # ==============================================================
        elif "entry" in payload:
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    changes_to_process.append(change)
            print("🌍 Processing Live WhatsApp Production Payload")

        # ==============================================================
        # 3. PROCESS THE EXTRACTED DATA
        # ==============================================================
        for change in changes_to_process:
            field = change.get("field")
            value = change.get("value", {})

            # -------------------------------------------------------------
            # SCENARIO A: Process Incoming "calls" Field
            # -------------------------------------------------------------
            if field == "calls":
                calls_list = value.get("calls", [])
                contacts_list = value.get("contacts", [])

                contact_map = {
                    c.get("wa_id"): c.get("profile", {}).get("name", "Unknown") 
                    for c in contacts_list if c.get("wa_id")
                }

                for call in calls_list:
                    call_id = call.get("id")
                    caller_phone = call.get("from")
                    call_event = call.get("event")
                    raw_timestamp = call.get("timestamp")
                    
                    date_time = datetime.fromtimestamp(int(raw_timestamp)) if raw_timestamp else datetime.utcnow()
                    caller_name = contact_map.get(caller_phone, "Unknown")
                    
                    await calls_collection.insert_one({
                        "call_id": call_id,
                        "caller_phone": caller_phone,
                        "wa_id": caller_phone,
                        "name": caller_name,
                        "call_event": call_event,
                        "date_time": date_time
                    })
                    print(f"🚨 Stored {call_event} call history log for {caller_name} ({caller_phone})")

            # -------------------------------------------------------------
            # SCENARIO B: Process Standard Core "messages" Field
            # -------------------------------------------------------------
            elif field == "messages":
                messages_list = value.get("messages", [])
                contacts_list = value.get("contacts", [])

                contact_map = {
                    c.get("wa_id"): c.get("profile", {}).get("name", "Unknown") 
                    for c in contacts_list if c.get("wa_id")
                }

                for msg in messages_list:
                    msg_id = msg.get("id")
                    sender = msg.get("from")
                    body = msg.get("text", {}).get("body", "[Non-text payload]")
                    
                    wa_id = sender 
                    name = contact_map.get(sender, "Unknown")
                    
                    # 1. Save the raw chat log
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
                    print(f"✅ Stored message and updated Task for {name} ({sender})")

            else:
                print(f"ℹ️ Received unhandled webhook field: {field}")
                        
    except Exception as e:
        print(f"❌ Webhook Processing Error: {e}")
        
    return {"status": "success"}
