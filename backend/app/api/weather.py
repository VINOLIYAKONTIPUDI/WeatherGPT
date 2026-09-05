from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.rbac import get_optional_user
from app.db.session import get_db
from app.models.entities import User
from app.services.location_service import LocationService
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["weather"])
weather = WeatherService()
locations = LocationService()


@router.get("/current")
async def current_weather(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    coords = await _coords(db, location, lat, lon, user)
    try:
        data = await weather.current(coords["latitude"], coords["longitude"])
    except Exception as exc:
        raise HTTPException(503, "Live weather data is temporarily unavailable. Please try again.") from exc
    return {"location": coords, **data}


@router.get("/forecast")
async def forecast(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    days: int = Query(7, ge=1, le=16),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    coords = await _coords(db, location, lat, lon, user)
    try:
        data = await weather.forecast(coords["latitude"], coords["longitude"], days)
    except Exception as exc:
        raise HTTPException(503, "Live weather data is temporarily unavailable. Please try again.") from exc
    return {"location": coords, **data}


async def _coords(db, location, lat, lon, user):
    if lat is not None and lon is not None:
        return {"name": location or "Coordinates", "latitude": lat, "longitude": lon}
    if location:
        hits = locations.search_db(db, location)
        if hits:
            h = hits[0]
            return {"name": h.name, "latitude": h.latitude, "longitude": h.longitude, "district": h.district, "state": h.state}
        remote = await weather.search_locations(location)
        if not remote:
            raise HTTPException(404, "Location not found")
        r = remote[0]
        loc = locations.get_or_create(db, r["name"], r["latitude"], r["longitude"], r.get("district"), r.get("state"))
        return {"name": loc.name, "latitude": loc.latitude, "longitude": loc.longitude, "district": loc.district, "state": loc.state}
    if user and user.locations:
        l = user.locations[0].location
        return {"name": l.name, "latitude": l.latitude, "longitude": l.longitude, "district": l.district, "state": l.state}
    vja = locations.default_vijayawada(db)
    if not vja:
        raise HTTPException(400, "Provide location or lat/lon")
    return {"name": vja.name, "latitude": vja.latitude, "longitude": vja.longitude, "district": vja.district, "state": vja.state}
