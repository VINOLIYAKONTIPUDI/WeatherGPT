from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional
from app.models.schemas import AlertsResponse, SMSBroadcastRequest, SMSBroadcastResponse
from app.services.weather_service import WeatherService
from app.services.advisory_service import AdvisoryService
from app.services.sms_service import SMSService

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
        return AdvisoryService.get_alerts_response(forecast)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/broadcast-sms", response_model=SMSBroadcastResponse)
async def broadcast_disaster_sms(payload: SMSBroadcastRequest):
    """
    Triggers an urgent disaster warning SMS broadcast to specified phone numbers
    or default emergency contacts during severe thunderstorms, heavy rainfall, or extreme heat.
    """
    try:
        res = await SMSService.dispatch_emergency_broadcast(
            phone_numbers=payload.phone_numbers,
            alert_type=payload.alert_type,
            location_name=payload.location_name,
            recommendation=payload.recommendation,
            severity=payload.severity
        )
        return SMSBroadcastResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to broadcast emergency SMS: {str(e)}")

