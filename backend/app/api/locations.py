from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.location_service import LocationService
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/locations", tags=["locations"])
locations = LocationService()
weather = WeatherService()


@router.get("/search")
async def search_locations(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    local = [
        {
            "id": loc.id,
            "name": loc.name,
            "district": loc.district,
            "state": loc.state,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "source": "db",
        }
        for loc in locations.search_db(db, q)
    ]
    remote = await weather.search_locations(q)
    return {"results": local + remote}
