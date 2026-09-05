from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.rbac import get_current_user, get_optional_user, require_roles
from app.db.session import get_db
from app.models.entities import Alert, User, UserRole
from app.schemas.api import DemoAlertRequest
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/alerts", tags=["alerts"])
alerts = AlertService()
notifications = NotificationService()
weather = WeatherService()


def _ser(a: Alert) -> dict:
    return {
        "id": a.id,
        "alert_type": a.alert_type,
        "severity": a.severity,
        "title": a.title,
        "description": a.description,
        "affected_location": a.affected_location,
        "district": a.district,
        "latitude": a.latitude,
        "longitude": a.longitude,
        "start_time": a.start_time,
        "end_time": a.end_time,
        "source": a.source,
        "cyclone_path": a.cyclone_path,
        "warning_zones": a.warning_zones,
        "is_demo": a.is_demo,
        "label": "DEMO DATA" if a.is_demo else "LIVE",
        "created_at": a.created_at,
    }


@router.get("")
def list_alerts(db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    return {"alerts": [_ser(a) for a in alerts.list_active(db)]}


@router.get("/nearby")
async def nearby_alerts(
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if lat is None or lon is None:
        if location:
            hits = await weather.search_locations(location)
            if hits:
                lat, lon = hits[0]["latitude"], hits[0]["longitude"]
        elif user and user.locations:
            lat, lon = user.locations[0].location.latitude, user.locations[0].location.longitude
        else:
            lat, lon = 16.5062, 80.6480
    return {"alerts": [_ser(a) for a in alerts.nearby(db, lat, lon)]}


@router.post("/demo")
def create_demo_alert(
    body: DemoAlertRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.disaster_manager, UserRole.admin)),
):
    now = datetime.utcnow()
    alert = alerts.ingest(
        db,
        {
            "alert_type": body.alert_type,
            "severity": body.severity,
            "title": f"{body.alert_type.title()} warning for {body.location}",
            "description": (
                f"[DEMO DATA] Simulated {body.alert_type} alert for {body.location}. "
                "Not an official IMD warning. Follow official safety instructions if a real event occurs."
            ),
            "affected_location": body.location,
            "latitude": 16.5062,
            "longitude": 80.6480,
            "start_time": now,
            "end_time": now + timedelta(hours=36),
            "source": "DEMO generator",
            "is_demo": True,
            "cyclone_path": {
                "points": [
                    {"lat": 15.0, "lon": 83.5, "t": "T+0"},
                    {"lat": 16.5, "lon": 80.65, "t": "T+24"},
                ]
            }
            if body.alert_type == "cyclone"
            else None,
        },
    )
    for u in alerts.matching_users(db, alert):
        notifications.create_for_alert(db, u, alert)
    return _ser(alert)
