from datetime import datetime, timedelta

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.entities import Alert, User
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService


def test_alert_match_and_notification():
    db = SessionLocal()
    try:
        init_db(db)
        user = db.query(User).filter(User.phone == "9999999999").first()
        assert user is not None
        svc = AlertService()
        nsvc = NotificationService()
        alert = svc.ingest(
            db,
            {
                "alert_type": "cyclone",
                "severity": "severe",
                "title": "Test cyclone",
                "description": "unit test",
                "affected_location": "Vijayawada",
                "district": "NTR",
                "latitude": 16.5062,
                "longitude": 80.6480,
                "start_time": datetime.utcnow(),
                "end_time": datetime.utcnow() + timedelta(hours=12),
                "source": "test",
                "is_demo": True,
            },
        )
        assert "[DEMO DATA]" in alert.title
        matched = svc.matching_users(db, alert)
        assert any(u.id == user.id for u in matched)
        n = nsvc.create_for_alert(db, user, alert)
        assert n.user_id == user.id
        assert "DEMO DATA" in n.message
    finally:
        db.close()
