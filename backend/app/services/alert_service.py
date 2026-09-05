import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import Alert, Notification, NotificationStatus, User, UserLocation

logger = logging.getLogger("weathergpt.alerts")


class AlertService:
    def list_active(self, db: Session) -> list[Alert]:
        now = datetime.utcnow()
        return (
            db.query(Alert)
            .filter((Alert.end_time.is_(None)) | (Alert.end_time >= now))
            .order_by(Alert.created_at.desc())
            .all()
        )

    def nearby(self, db: Session, lat: float, lon: float, radius_deg: float = 2.0) -> list[Alert]:
        alerts = self.list_active(db)
        out = []
        for a in alerts:
            if a.latitude is None or a.longitude is None:
                continue
            if abs(a.latitude - lat) <= radius_deg and abs(a.longitude - lon) <= radius_deg:
                out.append(a)
        return out

    def normalize(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "alert_type": payload.get("alert_type") or "unknown",
            "severity": payload.get("severity") or "moderate",
            "title": payload.get("title") or "Weather alert",
            "description": payload.get("description") or "",
            "affected_location": payload.get("affected_location") or payload.get("location") or "",
            "district": payload.get("district"),
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "start_time": payload.get("start_time"),
            "end_time": payload.get("end_time"),
            "source": payload.get("source") or "unknown",
            "cyclone_path": payload.get("cyclone_path"),
            "warning_zones": payload.get("warning_zones"),
            "is_demo": bool(payload.get("is_demo", True)),
        }

    def ingest(self, db: Session, payload: dict[str, Any]) -> Alert:
        data = self.normalize(payload)
        if data["is_demo"] and not str(data["title"]).startswith("[DEMO DATA]"):
            data["title"] = "[DEMO DATA] " + data["title"]
        alert = Alert(**data)
        db.add(alert)
        db.commit()
        db.refresh(alert)
        logger.info("alert_ingested id=%s type=%s demo=%s", alert.id, alert.alert_type, alert.is_demo)
        return alert

    def matching_users(self, db: Session, alert: Alert) -> list[User]:
        q = db.query(User).join(UserLocation).join(UserLocation.location)
        users: list[User] = []
        seen = set()
        for user in q.all():
            if user.id in seen:
                continue
            for ul in user.locations:
                loc = ul.location
                name_match = (
                    alert.affected_location
                    and loc.name.lower() in alert.affected_location.lower()
                ) or (alert.district and loc.district and alert.district.lower() == loc.district.lower())
                geo_match = False
                if alert.latitude is not None and alert.longitude is not None:
                    geo_match = abs(loc.latitude - alert.latitude) < 1.2 and abs(loc.longitude - alert.longitude) < 1.2
                if name_match or geo_match:
                    users.append(user)
                    seen.add(user.id)
                    break
        return users
