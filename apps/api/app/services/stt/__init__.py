from __future__ import annotations

import logging
from typing import AsyncIterator, Protocol

from app.core.config import Settings
from app.domain.models.provider import ProviderMode, TranscriptResult


class STTServiceProtocol(Protocol):
    async def start_stream(self, session_id: str) -> None: ...

    async def send_audio(self, audio_chunk: bytes) -> None: ...

    async def stop_stream(self) -> None: ...

    def set_input_sample_rate(self, sample_rate: int) -> None: ...

    def get_results(self) -> AsyncIterator[TranscriptResult]: ...


def get_openai_language_code(language_code: str) -> str:
    mapping = {
        "en-US": "en",
        "en-GB": "en",
        "ko-KR": "ko",
        "ja-JP": "ja",
    }
    return mapping.get(language_code, language_code.split("-")[0])


def create_stt_service(settings: Settings) -> STTServiceProtocol:
    logger = logging.getLogger(__name__)
    if settings.provider_mode == ProviderMode.AWS:
        from .aws import AWSSTTService

        logger.info("STT provider selected: AWS")
        return AWSSTTService(settings)
    if settings.provider_mode == ProviderMode.OPENAI:
        from .openai import OpenAISTTService

        logger.info("STT provider selected: OPENAI")
        return OpenAISTTService(settings)
    if settings.provider_mode == ProviderMode.GOOGLE:
        raise NotImplementedError("Google STT is planned for future release")
    raise ValueError(f"Unsupported provider: {settings.provider_mode}")
