from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/api/chat", tags=["Conversational Intelligence"])

@router.post("", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    try:
        return await AIService.process_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat query: {str(e)}")
