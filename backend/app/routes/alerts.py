import logging
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional
from app.models.schemas import AlertsResponse
from app.services.weather_service import WeatherService
from app.services.advisory_service import AdvisoryService
from app.services.email_service import EmailService
from app.core import security
from app.db.mongodb import db_instance

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["Weather Alerts & Advisories"])

@router.get("", response_model=AlertsResponse)
@router.post("", response_model=AlertsResponse)
async def get_weather_alerts(
    request: Request,
    lat: Optional[float] = Query(None, description="Latitude"),
    lon: Optional[float] = Query(None, description="Longitude"),
    name: Optional[str] = Query("Selected Location", description="Location Name")
):
    latitude = lat
    longitude = lon
    loc_name = name or "Selected Location"

    if (latitude is None or longitude is None) and request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict):
                latitude = body.get("latitude") if body.get("latitude") is not None else body.get("lat")
                longitude = body.get("longitude") if body.get("longitude") is not None else body.get("lon")
                loc_name = body.get("name") or body.get("city") or loc_name
        except Exception:
            pass

    if latitude is None or longitude is None:
        raise HTTPException(status_code=400, detail="Latitude and Longitude are required.")

    try:
        forecast = await WeatherService.get_forecast(latitude=latitude, longitude=longitude, location_name=loc_name)
        alerts_resp = AdvisoryService.get_alerts_response(forecast)
        
        # Check severe risk email trigger & deduplication
        if alerts_resp.smart_alert and alerts_resp.smart_alert.risk_score >= 75:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    token = auth_header.split(" ")[1]
                    payload = security.decode_access_token(token)
                    if payload and "email" in payload:
                        user_email = payload["email"]
                        today_str = datetime.now().strftime("%Y-%m-%d")
                        event_key = f"{user_email}_{loc_name}_{today_str}_severe"
                        
                        # Deduplication check
                        collection = db_instance.db["weather_alert_history"] if db_instance.db is not None else None
                        already_sent = False
                        if collection is not None:
                            existing = await collection.find_one({"event_key": event_key})
                            if existing:
                                already_sent = True
                        else:
                            already_sent = event_key in db_instance.in_memory_notifications
                        
                        if not already_sent:
                            # Record alert sent
                            if collection is not None:
                                await collection.insert_one({"event_key": event_key, "sent_at": datetime.now().isoformat()})
                            else:
                                db_instance.in_memory_notifications[event_key] = {"sent_at": datetime.now().isoformat()}

                            await EmailService.send_severe_weather_alert_email(
                                recipient_email=user_email,
                                user_name=payload.get("name", "User"),
                                location_name=loc_name,
                                smart_alert_dict=alerts_resp.smart_alert.dict()
                            )
                except Exception as ex:
                    logger.warning(f"Failed to process severe alert email: {ex}")

        return alerts_resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

