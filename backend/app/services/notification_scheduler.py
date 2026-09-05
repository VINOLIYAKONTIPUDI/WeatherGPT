import asyncio
import logging
from datetime import datetime
from app.db.mongodb import db_instance
from app.services.weather_service import WeatherService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

_scheduler_task: asyncio.Task = None

async def run_notification_scheduler():
    logger.info("⏰ Background Weather Notification Scheduler service started.")
    while True:
        try:
            await check_due_notifications()
        except Exception as e:
            logger.error(f"Error in notification scheduler loop: {e}")
        await asyncio.sleep(15)  # Check every 15 seconds

async def check_due_notifications():
    now_iso = datetime.now().isoformat()
    collection = db_instance.db["weather_notifications"] if db_instance.db is not None else None

    due_items = []

    if collection is not None:
        # Query MongoDB for pending schedules whose target time has arrived
        cursor = collection.find({
            "status": "pending",
            "scheduled_at": {"$lte": now_iso}
        })
        async for doc in cursor:
            due_items.append(doc)
    else:
        for notif_id, doc in list(db_instance.in_memory_notifications.items()):
            if doc.get("status") == "pending" and doc.get("scheduled_at", "") <= now_iso:
                due_items.append(doc)

    for item in due_items:
        notif_id = item["id"]
        user_email = item["user_email"]
        user_name = item.get("user_name", "User")
        notif_type = item.get("type", "full")
        loc_data = item.get("location") or {}
        loc_name = item.get("location_name") or loc_data.get("name") or loc_data.get("city") or "Selected Location"

        lat = float(loc_data.get("latitude", 17.385))
        lon = float(loc_data.get("longitude", 78.4866))

        # Atomically mark as processing to prevent duplicate emails
        if collection is not None:
            res = await collection.update_one(
                {"id": notif_id, "status": "pending"},
                {"$set": {"status": "processing"}}
            )
            if res.modified_count == 0:
                continue
        else:
            if db_instance.in_memory_notifications.get(notif_id, {}).get("status") == "pending":
                db_instance.in_memory_notifications[notif_id]["status"] = "processing"
            else:
                continue

        logger.info(f"🚀 Processing due weather notification [{notif_id}] for {user_email} ({loc_name})")

        try:
            # Fetch latest live weather forecast from Open-Meteo
            forecast = await WeatherService.get_forecast(lat, lon, loc_name)
            
            weather_dict = {
                "temperature": forecast.current.temperature,
                "condition": forecast.current.condition,
                "rain_probability": forecast.current.rain_probability,
                "humidity": forecast.current.relative_humidity,
                "wind_speed": forecast.current.wind_speed,
            }

            # Dispatch notification email via EmailService
            await EmailService.send_weather_notification_email(
                recipient_email=user_email,
                user_name=user_name,
                notif_type=notif_type,
                location_name=loc_name,
                weather_info=weather_dict
            )

            # Update status to sent
            final_status = "sent"
            sent_at = datetime.now().isoformat()

            if collection is not None:
                await collection.update_one(
                    {"id": notif_id},
                    {"$set": {"status": final_status, "sent_at": sent_at}}
                )
            else:
                if notif_id in db_instance.in_memory_notifications:
                    db_instance.in_memory_notifications[notif_id]["status"] = final_status
                    db_instance.in_memory_notifications[notif_id]["sent_at"] = sent_at

            logger.info(f"✅ Weather notification [{notif_id}] successfully delivered to {user_email}")

        except Exception as e:
            logger.error(f"❌ Failed to process notification [{notif_id}]: {e}")
            if collection is not None:
                await collection.update_one({"id": notif_id}, {"$set": {"status": "failed"}})
            elif notif_id in db_instance.in_memory_notifications:
                db_instance.in_memory_notifications[notif_id]["status"] = "failed"

def start_scheduler():
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(run_notification_scheduler())

def stop_scheduler():
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
