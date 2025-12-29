from __future__ import annotations

from fastapi import Request

from app.core.config import Settings
from app.services.bedrock import BedrockService
from app.services.suggestion import SuggestionService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_bedrock_service(request: Request) -> BedrockService:
    service = getattr(request.app.state, "bedrock_service", None)
    if service is None:
        service = BedrockService(request.app.state.settings)
        request.app.state.bedrock_service = service
    return service


def get_suggestion_service(request: Request) -> SuggestionService:
    service = getattr(request.app.state, "suggestion_service", None)
    if service is None:
        bedrock_service = get_bedrock_service(request)
        service = SuggestionService(bedrock_service, request.app.state.settings)
        request.app.state.suggestion_service = service
    return service
