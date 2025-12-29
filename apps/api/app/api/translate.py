from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_bedrock_service
from app.domain.models.translate import TranslateRequest, TranslateResponse
from app.services.bedrock import BedrockService

router = APIRouter()


@router.post("/translate/ko-en", response_model=TranslateResponse)
async def translate_ko_en(
    payload: TranslateRequest, bedrock_service: BedrockService = Depends(get_bedrock_service)
) -> TranslateResponse:
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    translated = await bedrock_service.translate_ko_to_en(text)
    return TranslateResponse(translated_text=translated)
