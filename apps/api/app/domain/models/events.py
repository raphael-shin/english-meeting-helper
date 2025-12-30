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
    segment_id: int


class TranscriptFinalEvent(BaseEvent):
    type: Literal["transcript.final"] = "transcript.final"
    session_id: str
    speaker: str
    text: str
    segment_id: int


class TranslationFinalEvent(BaseEvent):
    type: Literal["translation.final"] = "translation.final"
    session_id: str
    source_ts: int
    segment_id: int | None = None
    speaker: str
    source_text: str
    translated_text: str


class TranscriptCorrectedEvent(BaseEvent):
    type: Literal["transcript.corrected"] = "transcript.corrected"
    session_id: str
    segment_id: int
    original_text: str
    corrected_text: str


class TranslationCorrectedEvent(BaseEvent):
    type: Literal["translation.corrected"] = "translation.corrected"
    session_id: str
    segment_id: int
    speaker: str
    source_text: str
    translated_text: str


class SubtitleSegmentEvent(CamelModel):
    id: str
    text: str
    speaker: str
    start_time: int
    end_time: int | None
    is_final: bool
    llm_corrected: bool
    segment_id: int
    translation: str | None = None


class DisplayUpdateEvent(BaseEvent):
    type: Literal["display.update"] = "display.update"
    session_id: str
    confirmed: list[SubtitleSegmentEvent]
    current: SubtitleSegmentEvent | None


class SuggestionItem(CamelModel):
    en: str
    ko: str


class SuggestionsUpdateEvent(BaseEvent):
    type: Literal["suggestions.update"] = "suggestions.update"
    session_id: str
    items: list[SuggestionItem]


class SummaryUpdateEvent(BaseEvent):
    type: Literal["summary.update"] = "summary.update"
    session_id: str
    summary_markdown: str | None = None
    error: str | None = None


class ErrorEvent(BaseEvent):
    type: Literal["error"] = "error"
    code: str
    message: str
    retryable: bool | None = None
