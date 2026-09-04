from fastapi import APIRouter, Query, HTTPException
from app.models.schemas import AlertsResponse
from app.services.weather_service import WeatherService
from app.services.advisory_service import AdvisoryService

router = APIRouter(prefix="/api/alerts", tags=["Weather Alerts & Advisories"])

@router.get("", response_model=AlertsResponse)
@router.post("", response_model=AlertsResponse)
async def get_weather_alerts(
    lat: float = Query(17.3850, description="Latitude"),
    lon: float = Query(78.4867, description="Longitude"),
    name: str = Query("Selected Location", description="Location Name")
):
    try:
        forecast = await WeatherService.get_forecast(latitude=lat, longitude=lon, location_name=name)
        return AdvisoryService.get_alerts_response(forecast)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
