from __future__ import annotations

from fastapi import Request

from app.core.config import Settings
from app.services.stt import STTServiceProtocol, create_stt_service
from app.services.suggestion import SuggestionService
from app.services.translation import TranslationServiceProtocol, create_translation_service
from app.services.translation.aws import AWSTranslationService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_translation_service(request: Request) -> TranslationServiceProtocol:
    service = getattr(request.app.state, "translation_service", None)
    if service is None:
        service = create_translation_service(request.app.state.settings)
        request.app.state.translation_service = service
    return service


def get_stt_service(request: Request) -> STTServiceProtocol:
    service = getattr(request.app.state, "stt_service", None)
    if service is None:
        service = create_stt_service(request.app.state.settings)
        request.app.state.stt_service = service
    return service


def get_bedrock_service(request: Request) -> AWSTranslationService:
    service = getattr(request.app.state, "bedrock_service", None)
    if service is None:
        service = AWSTranslationService(request.app.state.settings)
        request.app.state.bedrock_service = service
    return service


def get_suggestion_service(request: Request) -> SuggestionService:
    service = getattr(request.app.state, "suggestion_service", None)
    if service is None:
        bedrock_service = get_bedrock_service(request)
        service = SuggestionService(bedrock_service, request.app.state.settings)
        request.app.state.suggestion_service = service
    return service
