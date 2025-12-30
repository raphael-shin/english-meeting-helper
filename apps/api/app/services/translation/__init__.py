from __future__ import annotations

import logging
from typing import Protocol

from app.core.config import Settings
from app.domain.models.provider import ProviderMode


class TranslationServiceProtocol(Protocol):
    async def translate_en_to_ko(self, text: str) -> str: ...

    async def translate_en_to_ko_history(
        self, text: str, recent_context: list[str] | None = None
    ) -> str: ...

    async def translate_ko_to_en(self, text: str) -> str: ...


def create_translation_service(settings: Settings) -> TranslationServiceProtocol:
    logger = logging.getLogger(__name__)
    if settings.provider_mode == ProviderMode.AWS:
        from .aws import AWSTranslationService

        logger.info("Translation provider selected: AWS")
        return AWSTranslationService(settings)
    if settings.provider_mode == ProviderMode.OPENAI:
        from .openai import OpenAITranslationService

        logger.info("Translation provider selected: OPENAI")
        return OpenAITranslationService(settings)
    if settings.provider_mode == ProviderMode.GOOGLE:
        raise NotImplementedError("Google Translation is planned for future release")
    raise ValueError(f"Unsupported provider: {settings.provider_mode}")
