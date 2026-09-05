from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.rbac import get_current_user
from app.db.session import get_db
from app.models.entities import User
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])
svc = NotificationService()


class ReadBody(BaseModel):
    id: int


@router.get("")
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = svc.list_for_user(db, user.id)
    return {
        "notifications": [
            {
                "id": n.id,
                "message": n.message,
                "status": n.status.value,
                "alert_id": n.alert_id,
                "created_at": n.created_at,
            }
            for n in items
        ]
    }


@router.post("/read")
def mark_read(body: ReadBody, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = svc.mark_read(db, user.id, body.id)
    if not n:
        raise HTTPException(404, "Notification not found")
    return {"id": n.id, "status": n.status.value}
