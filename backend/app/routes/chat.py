import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.ai_service import AIService
from app.constants.languages import normalize_language_code, get_language_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Conversational Intelligence"])

@router.post("", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    try:
        norm_lang = normalize_language_code(request.language)
        lang_name = get_language_name(norm_lang)
        logger.info(f"[ChatRoute] 📥 Received chat request | Language: '{request.language}' -> Normalized: '{norm_lang}' ({lang_name}) | Message: '{request.message}'")
        return await AIService.process_chat(request)
    except Exception as e:
        logger.error(f"[ChatRoute] ❌ Error processing chat query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process chat query: {str(e)}")
