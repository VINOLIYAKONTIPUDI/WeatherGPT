from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rbac import get_optional_user
from app.db.session import get_db
from app.models.entities import User
from app.schemas.api import VoiceTranscribeRequest
from app.services.ai_query_service import AIQueryService
from app.services.voice_service import VoiceService

router = APIRouter(prefix="/voice", tags=["voice"])
voice = VoiceService()
ai = AIQueryService()


@router.post("/transcribe")
async def transcribe(body: VoiceTranscribeRequest):
    return await voice.transcribe(body.language.value, body.text)


@router.post("/ask")
async def voice_ask(
    body: VoiceTranscribeRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    stt = await voice.transcribe(body.language.value, body.text)
    result = await ai.answer(db, stt["text"], body.language.value, None, user)
    tts = await voice.speak(result["answer"], body.language.value)
    return {"stt": stt, "chat": result, "tts": tts}
