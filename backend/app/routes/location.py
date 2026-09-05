from fastapi import APIRouter, Query, HTTPException
from typing import List
from app.models.schemas import LocationSearchResult, LocationCoordinates
from app.services.geocoding_service import GeocodingService

router = APIRouter(prefix="/api/location", tags=["Geocoding & Location Search"])

@router.get("/search", response_model=List[LocationSearchResult])
async def search_location(q: str = Query("", description="City or place name")):
    return await GeocodingService.search_location(q)

@router.get("/reverse", response_model=LocationCoordinates)
async def reverse_geocode(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    return await GeocodingService.reverse_geocode(lat, lon)
