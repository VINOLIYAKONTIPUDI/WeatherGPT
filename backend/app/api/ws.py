from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.entities import Notification, User
from app.services.notification_service import NotificationService

router = APIRouter()


@router.websocket("/ws/notifications")
async def notifications_ws(ws: WebSocket):
    await ws.accept()
    token = ws.query_params.get("token")
    payload = decode_access_token(token) if token else None
    if not payload:
        await ws.send_json({"error": "unauthorized"})
        await ws.close()
        return
    db: Session = SessionLocal()
    try:
        user = db.get(User, int(payload["sub"]))
        if not user:
            await ws.close()
            return
        items = NotificationService().list_for_user(db, user.id)
        await ws.send_json(
            {
                "type": "snapshot",
                "notifications": [
                    {"id": n.id, "message": n.message, "status": n.status.value} for n in items[:10]
                ],
            }
        )
        await ws.receive_text()
    except WebSocketDisconnect:
        return
    finally:
        db.close()
