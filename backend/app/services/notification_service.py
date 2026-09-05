import logging
from typing import Protocol

from sqlalchemy.orm import Session

from app.models.entities import Alert, Notification, NotificationStatus, User

logger = logging.getLogger("weathergpt.notifications")


class PushChannel(Protocol):
    async def send(self, user: User, message: str) -> None: ...


class InAppChannel:
    """MVP channel. FCM/SMS can implement the same protocol later."""

    name = "in_app"

    async def send(self, user: User, message: str) -> None:
        return None


class FCMChannelStub:
    name = "fcm"

    async def send(self, user: User, message: str) -> None:
        logger.info("fcm_stub_skipped user_id=%s (not configured)", user.id)


class NotificationService:
    def __init__(self, channels: list[PushChannel] | None = None) -> None:
        self.channels = channels or [InAppChannel()]

    def create_for_alert(self, db: Session, user: User, alert: Alert) -> Notification:
        prefix = "🚨 Severe Weather Alert"
        extra = " [DEMO DATA]" if alert.is_demo else ""
        msg = (
            f"{prefix}{extra}: {alert.title}. "
            f"{alert.description[:240]} Please follow official safety instructions."
        )
        n = Notification(user_id=user.id, alert_id=alert.id, message=msg, status=NotificationStatus.unread)
        db.add(n)
        try:
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("notification_create_failed user_id=%s alert_id=%s", user.id, alert.id)
            raise
        db.refresh(n)
        return n

    def list_for_user(self, db: Session, user_id: int) -> list[Notification]:
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(50)
            .all()
        )

    def mark_read(self, db: Session, user_id: int, notification_id: int) -> Notification | None:
        n = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if not n:
            return None
        n.status = NotificationStatus.read
        db.commit()
        db.refresh(n)
        return n
