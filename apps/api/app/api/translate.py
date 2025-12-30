from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_translation_service
from app.domain.models.translate import TranslateRequest, TranslateResponse
from app.services.translation import TranslationServiceProtocol

router = APIRouter()


@router.post("/translate/ko-en", response_model=TranslateResponse)
async def translate_ko_en(
    payload: TranslateRequest,
    translation_service: TranslationServiceProtocol = Depends(get_translation_service),
) -> TranslateResponse:
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    translated = await translation_service.translate_ko_to_en(text)
    return TranslateResponse(translated_text=translated)
