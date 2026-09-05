from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rbac import get_optional_user
from app.db.session import get_db
from app.models.entities import User
from app.schemas.api import ChatRequest, ChatResponse
from app.services.ai_query_service import AIQueryService

router = APIRouter(tags=["chat"])
ai = AIQueryService()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    lang = body.language.value if body.language else (user.preferred_language.value if user else "en")
    result = await ai.answer(
        db,
        body.message,
        lang,
        body.location,
        user,
        body.latitude,
        body.longitude,
    )
    return ChatResponse(**result)
