from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any, AsyncIterator

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import Settings
from app.domain.models.events import (
    ErrorEvent,
    SessionStopEvent,
    SuggestionsUpdateEvent,
    TranscriptFinalEvent,
    TranscriptPartialEvent,
    TranslationFinalEvent,
)
from app.domain.models.session import MeetingSession
from app.domain.models.base import epoch_ms
from app.services.bedrock import BedrockService
from app.services.suggestion import SuggestionService
from app.services.transcribe import TranscribeService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/v1/meetings/{session_id}")
async def meeting_ws(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    if not session_id:
        await _send_error(websocket, "SESSION_NOT_FOUND", "sessionId is required")
        await websocket.close()
        return

    settings: Settings = websocket.app.state.settings
    bedrock_service: BedrockService | None = getattr(websocket.app.state, "bedrock_service", None)
    if bedrock_service is None:
        bedrock_service = BedrockService(settings)
        websocket.app.state.bedrock_service = bedrock_service
    suggestion_service: SuggestionService | None = getattr(websocket.app.state, "suggestion_service", None)
    if suggestion_service is None:
        suggestion_service = SuggestionService(bedrock_service, settings)
        websocket.app.state.suggestion_service = suggestion_service
    session = MeetingSession(session_id)
    transcribe_service = TranscribeService(settings)
    send_lock = asyncio.Lock()

    async def send_payload(payload: dict[str, Any]) -> None:
        async with send_lock:
            await websocket.send_text(json.dumps(payload))

    async def send_event(event: Any) -> None:
        await send_payload(event.model_dump(by_alias=True))

    async def handle_transcribe_events(events: AsyncIterator[Any]) -> None:
        try:
            async for event in events:
                try:
                    for is_partial, speaker, text in _parse_transcribe_event(event):
                        ts = epoch_ms()
                        if is_partial:
                            await send_event(
                                TranscriptPartialEvent(
                                    session_id=session_id,
                                    speaker=speaker,
                                    ts=ts,
                                    text=text,
                                )
                            )
                            partial_candidate = session.extract_partial_translation(speaker, ts, text)
                            if partial_candidate:
                                try:
                                    translated = await bedrock_service.translate_en_to_ko(partial_candidate)
                                except Exception:
                                    logger.exception("Bedrock translation failed")
                                    await _send_error(websocket, "BEDROCK_ERROR", "Translation failed")
                                else:
                                    await send_event(
                                        TranslationFinalEvent(
                                            session_id=session_id,
                                            source_ts=ts,
                                            speaker=speaker,
                                            source_text=partial_candidate,
                                            translated_text=translated,
                                        )
                                    )
                            continue

                        chunks, remainder = session.add_final_transcript(speaker, text)
                        speaker_changed_any = False
                        if chunks:
                            base_ts = epoch_ms()
                            for index, chunk in enumerate(chunks):
                                chunk_ts = base_ts + index
                                speaker_changed = session.add_final_chunk(speaker, chunk_ts, chunk)
                                speaker_changed_any = speaker_changed_any or speaker_changed
                                await send_event(
                                    TranscriptFinalEvent(
                                        session_id=session_id,
                                        speaker=speaker,
                                        ts=chunk_ts,
                                        text=chunk,
                                    )
                                )
                                try:
                                    translated = await bedrock_service.translate_en_to_ko(chunk)
                                except Exception:
                                    logger.exception("Bedrock translation failed")
                                    await _send_error(websocket, "BEDROCK_ERROR", "Translation failed")
                                    continue

                                session.add_translation(speaker, chunk_ts, chunk, translated)
                                await send_event(
                                    TranslationFinalEvent(
                                        session_id=session_id,
                                        source_ts=chunk_ts,
                                        speaker=speaker,
                                        source_text=chunk,
                                        translated_text=translated,
                                    )
                                )

                        if remainder:
                            await send_event(
                                TranscriptPartialEvent(
                                    session_id=session_id,
                                    speaker=speaker,
                                    ts=ts,
                                    text=remainder,
                                )
                            )
                            partial_candidate = session.extract_partial_translation(speaker, ts, remainder)
                            if partial_candidate:
                                try:
                                    translated = await bedrock_service.translate_en_to_ko(partial_candidate)
                                except Exception:
                                    logger.exception("Bedrock translation failed")
                                    await _send_error(websocket, "BEDROCK_ERROR", "Translation failed")
                                else:
                                    await send_event(
                                        TranslationFinalEvent(
                                            session_id=session_id,
                                            source_ts=ts,
                                            speaker=speaker,
                                            source_text=partial_candidate,
                                            translated_text=translated,
                                        )
                                    )

                        if chunks and session.should_update_suggestions(speaker_changed_any):
                            suggestions = await suggestion_service.generate_suggestions(
                                session.recent_transcripts(),
                                session.suggestions_prompt,
                            )
                            if suggestions:
                                await send_event(
                                    SuggestionsUpdateEvent(
                                        session_id=session_id,
                                        items=suggestions,
                                    )
                                )
                                session.mark_suggestions_updated()
                except Exception:
                    logger.exception("Transcribe stream handling failed")
                    await _send_error(websocket, "TRANSCRIBE_STREAM_ERROR", "Upstream streaming error")
                    break
        except asyncio.CancelledError:
            return

    try:
        await transcribe_service.start_stream(session_id)
    except Exception:
        logger.exception("Failed to start transcribe stream")
        await _send_error(websocket, "TRANSCRIBE_STREAM_ERROR", "Failed to start transcription")
        await websocket.close()
        return

    results_task = asyncio.create_task(handle_transcribe_events(transcribe_service.get_results()))

    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if message.get("text") is not None:
                await _handle_control_message(message["text"], send_payload, session)
                if _is_session_stop(message["text"]):
                    await send_event(SessionStopEvent())
                    break
            elif message.get("bytes") is not None:
                await transcribe_service.send_audio(message["bytes"])
    except WebSocketDisconnect:
        return
    finally:
        with contextlib.suppress(Exception):
            await transcribe_service.stop_stream()
        try:
            await asyncio.wait_for(results_task, timeout=1.0)
        except asyncio.TimeoutError:
            results_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await results_task


async def _handle_control_message(raw_text: str, send_payload, session: MeetingSession) -> None:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        await _send_invalid_message(send_payload, "Invalid JSON control message")
        return

    message_type = payload.get("type")
    if message_type == "client.ping":
        await send_payload({"type": "server.pong", "ts": epoch_ms()})
        return
    if message_type == "suggestions.prompt":
        prompt = payload.get("prompt", "")
        if not isinstance(prompt, str):
            await _send_invalid_message(send_payload, "Invalid suggestions prompt")
            return
        session.set_suggestions_prompt(prompt)
        return
    if message_type in {"session.start", "session.stop"}:
        return

    await _send_invalid_message(send_payload, "Unknown control message type")


def _is_session_stop(raw_text: str) -> bool:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return False
    return payload.get("type") == "session.stop"


async def _send_invalid_message(send_payload, message: str) -> None:
    event = ErrorEvent(code="INVALID_MESSAGE", message=message)
    await send_payload(event.model_dump(by_alias=True))


async def _send_error(websocket: WebSocket, code: str, message: str) -> None:
    event = ErrorEvent(code=code, message=message)
    await websocket.send_text(json.dumps(event.model_dump(by_alias=True)))


def _parse_transcribe_event(event: Any) -> list[tuple[bool, str, str]]:
    results: list[Any] = []
    transcript = getattr(event, "transcript", None)
    if transcript is not None and hasattr(transcript, "results"):
        results = list(transcript.results)
    elif isinstance(event, dict):
        transcript = event.get("Transcript") or event.get("transcript") or {}
        results = transcript.get("Results") or transcript.get("results") or []

    parsed: list[tuple[bool, str, str]] = []
    for result in results:
        is_partial = _get_attr(result, "is_partial", "IsPartial", "isPartial")
        if is_partial is None:
            is_partial = False
        alternatives = _get_attr(result, "alternatives", "Alternatives", "alternatives") or []
        if not alternatives:
            continue
        alternative = alternatives[0]
        text = _get_attr(alternative, "transcript", "Transcript", "transcript")
        if not text:
            continue
        speaker = _extract_speaker(alternative)
        parsed.append((bool(is_partial), speaker, str(text)))
    return parsed


def _get_attr(obj: Any, *names: str) -> Any:
    if isinstance(obj, dict):
        for name in names:
            if name in obj:
                return obj[name]
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def _extract_speaker(alternative: Any) -> str:
    items = _get_attr(alternative, "items", "Items", "items") or []
    for item in items:
        speaker = _get_attr(item, "speaker", "Speaker", "speaker_label", "speakerLabel")
        if speaker is not None:
            speaker_value = str(speaker)
            if not speaker_value.startswith("spk_"):
                return f"spk_{speaker_value}"
            return speaker_value
    return "spk_1"
