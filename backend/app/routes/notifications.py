import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, status

from app.models.schemas import ScheduleNotificationRequest, NotificationItemResponse
from app.core import security
from app.routes.auth import find_user_by_email
from app.db.mongodb import db_instance

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Weather Notifications"])

def get_notifications_collection():
    if db_instance.db is not None:
        return db_instance.db["weather_notifications"]
    return None

async def authenticate_user(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication token required.")
    token = authorization.split(" ")[1]
    payload = security.decode_access_token(token)
    if not payload or "email" not in payload:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    user = await find_user_by_email(payload["email"])
    if not user:
        raise HTTPException(status_code=401, detail="User account not found.")
    return user

def calculate_scheduled_iso(target_date: str, target_time: str) -> datetime:
    now = datetime.now()
    
    # 1. Determine target date object
    clean_date = target_date.strip().lower()
    if clean_date in ["today"]:
        base_date = now.date()
    elif clean_date in ["tomorrow"]:
        base_date = (now + timedelta(days=1)).date()
    elif clean_date in ["day after tomorrow"]:
        base_date = (now + timedelta(days=2)).date()
    else:
        try:
            base_date = datetime.strptime(target_date.strip(), "%Y-%m-%d").date()
        except Exception:
            base_date = now.date()

    # 2. Determine target time (HH:MM)
    try:
        parts = target_time.strip().split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
    except Exception:
        hours = now.hour
        minutes = now.minute

    target_dt = datetime(
        year=base_date.year,
        month=base_date.month,
        day=base_date.day,
        hour=hours,
        minute=minutes,
        second=0
    )
    return target_dt

@router.post("/schedule", response_model=NotificationItemResponse)
async def schedule_notification(
    request: ScheduleNotificationRequest,
    authorization: Optional[str] = Header(None)
):
    user = await authenticate_user(authorization)
    
    target_dt = calculate_scheduled_iso(request.target_date, request.target_time)
    now_dt = datetime.now()
    
    # Allow small 10-second grace period for scheduling slightly in the past/immediate
    if target_dt < (now_dt - timedelta(seconds=10)):
        raise HTTPException(status_code=400, detail="Scheduled time must be in the future.")

    notif_id = f"notif_{uuid.uuid4().hex[:10]}"
    loc_dict = request.location.dict() if request.location else None
    loc_name = request.location.displayName or request.location.name if request.location else "Selected Location"

    notif_doc = {
        "id": notif_id,
        "user_email": user["email"],
        "user_name": user.get("name", "User"),
        "target_date": request.target_date,
        "target_time": request.target_time,
        "scheduled_at": target_dt.isoformat(),
        "type": request.type,  # 'rain', 'temperature', 'full'
        "status": "pending",   # 'pending', 'processing', 'sent', 'failed'
        "location": loc_dict,
        "location_name": loc_name,
        "created_at": datetime.now().isoformat()
    }

    collection = get_notifications_collection()
    if collection is not None:
        await collection.insert_one(notif_doc)
    else:
        db_instance.in_memory_notifications[notif_id] = notif_doc

    logger.info(f"Scheduled weather notification {notif_id} for {user['email']} at {target_dt.isoformat()}")

    return NotificationItemResponse(
        id=notif_id,
        user_email=user["email"],
        user_name=user.get("name", "User"),
        target_date=request.target_date,
        target_time=request.target_time,
        scheduled_at=target_dt.isoformat(),
        type=request.type,
        status="pending",
        location_name=loc_name,
        created_at=notif_doc["created_at"]
    )

@router.get("", response_model=List[NotificationItemResponse])
async def get_user_notifications(authorization: Optional[str] = Header(None)):
    user = await authenticate_user(authorization)
    user_email = user["email"]

    collection = get_notifications_collection()
    items = []

    if collection is not None:
        cursor = collection.find({"user_email": user_email}).sort("created_at", -1)
        async for doc in cursor:
            items.append(NotificationItemResponse(
                id=doc["id"],
                user_email=doc["user_email"],
                user_name=doc.get("user_name", "User"),
                target_date=doc.get("target_date", "Today"),
                target_time=doc.get("target_time", "08:00"),
                scheduled_at=doc.get("scheduled_at", ""),
                type=doc.get("type", "full"),
                status=doc.get("status", "pending"),
                location_name=doc.get("location_name", "Selected Location"),
                created_at=doc.get("created_at", "")
            ))
    else:
        for notif_id, doc in db_instance.in_memory_notifications.items():
            if doc.get("user_email") == user_email:
                items.append(NotificationItemResponse(
                    id=doc["id"],
                    user_email=doc["user_email"],
                    user_name=doc.get("user_name", "User"),
                    target_date=doc.get("target_date", "Today"),
                    target_time=doc.get("target_time", "08:00"),
                    scheduled_at=doc.get("scheduled_at", ""),
                    type=doc.get("type", "full"),
                    status=doc.get("status", "pending"),
                    location_name=doc.get("location_name", "Selected Location"),
                    created_at=doc.get("created_at", "")
                ))
        items.sort(key=lambda x: x.created_at, reverse=True)

    return items

@router.delete("/{notif_id}")
async def delete_notification(
    notif_id: str,
    authorization: Optional[str] = Header(None)
):
    user = await authenticate_user(authorization)
    user_email = user["email"]

    collection = get_notifications_collection()
    if collection is not None:
        res = await collection.delete_one({"id": notif_id, "user_email": user_email})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found.")
    else:
        if notif_id in db_instance.in_memory_notifications:
            doc = db_instance.in_memory_notifications[notif_id]
            if doc.get("user_email") == user_email:
                del db_instance.in_memory_notifications[notif_id]
            else:
                raise HTTPException(status_code=403, detail="Unauthorized access.")
        else:
            raise HTTPException(status_code=404, detail="Notification not found.")

    return {"status": "success", "message": "Notification cancelled successfully."}
