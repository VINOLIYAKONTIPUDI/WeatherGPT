from fastapi import APIRouter, Query, HTTPException
from app.models.schemas import WeatherForecastResponse
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/api/weather", tags=["Weather"])

@router.get("/forecast", response_model=WeatherForecastResponse)
async def get_weather_forecast(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    name: str = Query("Selected Location", description="Location Name")
):
    try:
        return await WeatherService.get_forecast(latitude=lat, longitude=lon, location_name=name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current")
async def get_current_weather(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    name: str = Query("Selected Location", description="Location Name")
):
    forecast = await WeatherService.get_forecast(latitude=lat, longitude=lon, location_name=name)
    return {
        "location": forecast.location,
        "current": forecast.current,
        "is_fallback": forecast.is_fallback
    }
