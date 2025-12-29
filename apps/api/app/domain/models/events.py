from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import CamelModel, epoch_ms


class BaseEvent(CamelModel):
    type: str
    ts: int = Field(default_factory=epoch_ms)


class SessionStartEvent(BaseEvent):
    type: Literal["session.start"] = "session.start"
    sample_rate: int
    format: str
    lang: str


class SessionStopEvent(BaseEvent):
    type: Literal["session.stop"] = "session.stop"


class TranscriptPartialEvent(BaseEvent):
    type: Literal["transcript.partial"] = "transcript.partial"
    session_id: str
    speaker: str
    text: str


class TranscriptFinalEvent(BaseEvent):
    type: Literal["transcript.final"] = "transcript.final"
    session_id: str
    speaker: str
    text: str


class TranslationFinalEvent(BaseEvent):
    type: Literal["translation.final"] = "translation.final"
    session_id: str
    source_ts: int
    speaker: str
    source_text: str
    translated_text: str


class SuggestionItem(CamelModel):
    en: str
    ko: str


class SuggestionsUpdateEvent(BaseEvent):
    type: Literal["suggestions.update"] = "suggestions.update"
    session_id: str
    items: list[SuggestionItem]


class ErrorEvent(BaseEvent):
    type: Literal["error"] = "error"
    code: str
    message: str
    retryable: bool | None = None
