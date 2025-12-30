from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time
from typing import Any, AsyncIterator

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import Settings
from app.core.logging import log_event
from app.domain.models.events import (
    DisplayUpdateEvent,
    ErrorEvent,
    SessionStopEvent,
    SubtitleSegmentEvent,
    SuggestionsUpdateEvent,
    TranscriptCorrectedEvent,
    TranscriptFinalEvent,
    TranscriptPartialEvent,
    TranslationCorrectedEvent,
    TranslationFinalEvent,
)
from app.domain.models.session import MeetingSession
from app.domain.models.base import epoch_ms
from app.domain.models.provider import TranscriptResult
from app.domain.models.subtitle import SubtitleSegment
from app.services.stt import STTServiceProtocol, create_stt_service
from app.services.suggestion import SuggestionService
from app.services.correction import CorrectionQueue
from app.services.translation import TranslationServiceProtocol, create_translation_service
from app.services.translation.aws import AWSTranslationService

router = APIRouter()
logger = logging.getLogger(__name__)
_HISTORY_CONTEXT_SENTENCES = 5
_LOG_SAMPLE_PARTIAL = 0.05
_LOG_SAMPLE_PING = 0.1

@router.websocket("/ws/v1/meetings/{session_id}")
async def meeting_ws(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    if not session_id:
        await _send_error(websocket, "SESSION_NOT_FOUND", "sessionId is required")
        await websocket.close()
        return

    settings: Settings = websocket.app.state.settings
    log_event(
        logger,
        "ws.connected",
        session_id=session_id,
        provider_mode=settings.provider_mode.value,
    )
    translation_service: TranslationServiceProtocol | None = getattr(
        websocket.app.state, "translation_service", None
    )
    if translation_service is None:
        translation_service = create_translation_service(settings)
        websocket.app.state.translation_service = translation_service
    bedrock_service: AWSTranslationService | None = getattr(websocket.app.state, "bedrock_service", None)
    if bedrock_service is None:
        bedrock_service = AWSTranslationService(settings)
        websocket.app.state.bedrock_service = bedrock_service
    suggestion_service: SuggestionService | None = getattr(websocket.app.state, "suggestion_service", None)
    if suggestion_service is None:
        suggestion_service = SuggestionService(bedrock_service, settings)
        websocket.app.state.suggestion_service = suggestion_service
    session = MeetingSession(session_id)
    transcribe_service = create_stt_service(settings)
    correction_queue: CorrectionQueue | None = None
    if settings.llm_correction_enabled:
        correction_queue = CorrectionQueue(
            bedrock_service,
            batch_size=settings.llm_correction_batch_size,
        )
    send_lock = asyncio.Lock()
    is_closing = False
    background_tasks: set[asyncio.Task] = set()
    translation_semaphore = asyncio.Semaphore(2)
    suggestion_semaphore = asyncio.Semaphore(1)

    async def send_payload(payload: dict[str, Any]) -> None:
        if is_closing:
            return
        async with send_lock:
            try:
                await websocket.send_text(json.dumps(payload))
            except (WebSocketDisconnect, RuntimeError):
                return

    async def send_event(event: Any) -> None:
        await send_payload(event.model_dump(by_alias=True))

    def _segment_to_event(segment: SubtitleSegment) -> SubtitleSegmentEvent:
        return SubtitleSegmentEvent(
            id=segment.id,
            text=segment.text,
            speaker=segment.speaker,
            start_time=segment.start_time,
            end_time=segment.end_time,
            is_final=segment.is_final,
            llm_corrected=segment.llm_corrected,
            segment_id=segment.segment_id,
        )

    async def send_display_update() -> None:
        buffer = session.get_display_buffer()
        await send_event(
            DisplayUpdateEvent(
                session_id=session_id,
                confirmed=[_segment_to_event(seg) for seg in buffer.confirmed],
                current=_segment_to_event(buffer.current) if buffer.current else None,
            )
        )

    def _build_partial_segment(
        partial_emit_text: str,
        partial_segment_id: int,
        ts: int,
        speaker: str,
    ) -> SubtitleSegment:
        display_buffer = session.get_display_buffer()
        current = display_buffer.current
        if current and not current.is_final and current.segment_id == partial_segment_id:
            return SubtitleSegment(
                id=current.id,
                text=partial_emit_text,
                speaker=speaker,
                start_time=current.start_time,
                end_time=None,
                is_final=False,
                llm_corrected=False,
                segment_id=current.segment_id,
            )
        return SubtitleSegment(
            id=f"seg_{partial_segment_id}",
            text=partial_emit_text,
            speaker=speaker,
            start_time=ts,
            end_time=None,
            is_final=False,
            llm_corrected=False,
            segment_id=partial_segment_id,
        )

    def track_task(task: asyncio.Task) -> None:
        background_tasks.add(task)
        task.add_done_callback(_on_task_done)

    def _on_task_done(task: asyncio.Task) -> None:
        background_tasks.discard(task)
        with contextlib.suppress(asyncio.CancelledError):
            exc = task.exception()
            if exc:
                logger.exception("Background task failed", exc_info=exc)

    async def translate_partial_text(
        source_text: str,
        ts: int,
        speaker: str,
        segment_id: int,
    ) -> None:
        if is_closing:
            return
        async with translation_semaphore:
            started = time.perf_counter()
            try:
                translated = await translation_service.translate_en_to_ko(source_text)
            except Exception:
                logger.exception("Translation failed")
                await send_event(
                    ErrorEvent(code="BEDROCK_ERROR", message="Translation failed")
                )
                return
            if not session.is_partial_translation_current(
                speaker,
                ts,
                source_text,
                segment_id,
            ):
                return
            log_event(
                logger,
                "translation.final",
                session_id=session_id,
                segment_id=segment_id,
                text_len=len(source_text),
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
            await send_event(
                TranslationFinalEvent(
                    session_id=session_id,
                    source_ts=ts,
                    segment_id=segment_id,
                    speaker=speaker,
                    source_text=source_text,
                    translated_text=translated,
                )
            )

    async def translate_final_text(
        source_text: str,
        ts: int,
        speaker: str,
        recent_context: list[str] | None = None,
        segment_id: int | None = None,
    ) -> None:
        if is_closing:
            return
        async with translation_semaphore:
            started = time.perf_counter()
            try:
                translated = await translation_service.translate_en_to_ko_history(
                    source_text,
                    recent_context,
                )
            except Exception:
                logger.exception("Translation failed")
                await send_event(
                    ErrorEvent(code="BEDROCK_ERROR", message="Translation failed")
                )
                return

            session.add_translation(speaker, ts, source_text, translated)
            log_event(
                logger,
                "translation.final",
                session_id=session_id,
                segment_id=segment_id,
                text_len=len(source_text),
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
            await send_event(
                TranslationFinalEvent(
                    session_id=session_id,
                    source_ts=ts,
                    segment_id=segment_id,
                    speaker=speaker,
                    source_text=source_text,
                    translated_text=translated,
                )
            )

    async def translate_corrected_text(
        corrected_text: str,
        segment_id: int,
    ) -> None:
        if is_closing:
            return
        async with translation_semaphore:
            started = time.perf_counter()
            try:
                translated = await translation_service.translate_en_to_ko_history(
                    corrected_text,
                    None,
                )
            except Exception:
                logger.exception("Corrected translation failed")
                await send_event(
                    ErrorEvent(code="BEDROCK_ERROR", message="Corrected translation failed")
                )
                return
            log_event(
                logger,
                "translation.corrected",
                session_id=session_id,
                segment_id=segment_id,
                text_len=len(corrected_text),
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
            await send_event(
                TranslationCorrectedEvent(
                    session_id=session_id,
                    segment_id=segment_id,
                    speaker="spk_1",
                    source_text=corrected_text,
                    translated_text=translated,
                )
            )

    async def process_corrections() -> None:
        if correction_queue is None:
            return
        while not is_closing:
            try:
                corrections = await correction_queue.process_batch()
                for segment_id, original, corrected in corrections:
                    await send_event(
                        TranscriptCorrectedEvent(
                            session_id=session_id,
                            segment_id=segment_id,
                            original_text=original,
                            corrected_text=corrected,
                        )
                    )
                    track_task(
                        asyncio.create_task(
                            translate_corrected_text(
                                corrected_text=corrected,
                                segment_id=segment_id,
                            )
                        )
                    )
            except Exception:
                logger.exception("Correction processing failed")
            await asyncio.sleep(settings.llm_correction_interval_seconds)

    async def generate_and_send_suggestions(
        transcripts: list[Any], prompt: str | None
    ) -> None:
        if is_closing:
            return
        if suggestion_semaphore.locked():
            return
        async with suggestion_semaphore:
            started = time.perf_counter()
            try:
                suggestions = await suggestion_service.generate_suggestions(
                    transcripts,
                    prompt,
                )
            except Exception:
                logger.exception("Suggestion generation failed")
                await send_event(
                    ErrorEvent(code="SUGGESTION_ERROR", message="Suggestions failed")
                )
                return
            if not suggestions:
                return
            log_event(
                logger,
                "suggestions.update",
                session_id=session_id,
                item_count=len(suggestions),
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
            await send_event(
                SuggestionsUpdateEvent(
                    session_id=session_id,
                    items=suggestions,
                )
            )
            session.mark_suggestions_updated()

    async def handle_transcribe_events(events: AsyncIterator[TranscriptResult]) -> None:
        try:
            async for result in events:
                try:
                    ts = epoch_ms()
                    speaker = "spk_1"
                    if result.is_partial:
                        logger.info(f"[PARTIAL_RAW] text_len={len(result.text)} text=\"{result.text[:100]}...\"" if len(result.text) > 100 else f"[PARTIAL_RAW] text_len={len(result.text)} text=\"{result.text}\"")
                        partial_emit = session.extract_partial_emit(speaker, ts, result.text)
                        if not partial_emit:
                            continue
                        segment = _build_partial_segment(
                            partial_emit_text=partial_emit.caption_text,
                            partial_segment_id=partial_emit.segment_id,
                            ts=ts,
                            speaker=speaker,
                        )
                        session.update_display_buffer(segment)
                        await send_display_update()
                        log_event(
                            logger,
                            "stt.partial",
                            session_id=session_id,
                            segment_id=partial_emit.segment_id,
                            text_len=len(partial_emit.caption_text),
                            sample_rate=_LOG_SAMPLE_PARTIAL,
                        )
                        await send_event(
                            TranscriptPartialEvent(
                                session_id=session_id,
                                speaker=speaker,
                                ts=ts,
                                text=partial_emit.caption_text,
                                segment_id=partial_emit.segment_id,
                            )
                        )
                        continue

                    # Process final transcript as single segment (no chunking)
                    text, segment_id = session.add_final_transcript(speaker, result.text, ts)
                    
                    # Get start time from current partial if exists
                    display_buffer = session.get_display_buffer()
                    current = display_buffer.current
                    start_time = current.start_time if current and current.segment_id == segment_id else ts
                    
                    # Create final segment
                    segment = SubtitleSegment(
                        id=f"seg_{segment_id}",
                        text=text,
                        speaker=speaker,
                        start_time=start_time,
                        end_time=ts,
                        is_final=True,
                        llm_corrected=False,
                        segment_id=segment_id,
                    )
                    
                    logger.info(f"[FINAL] segmentId={segment_id} text=\"{text[:100]}...\"" if len(text) > 100 else f"[FINAL] segmentId={segment_id} text=\"{text}\" is_final={segment.is_final}")
                    
                    # Update display buffer
                    session.update_display_buffer(segment)
                    await send_display_update()
                    
                    # Enqueue for LLM correction
                    if correction_queue is not None:
                        await correction_queue.enqueue(segment)
                    
                    # Log event
                    log_event(
                        logger,
                        "stt.final",
                        session_id=session_id,
                        segment_id=segment_id,
                        text_len=len(text),
                    )
                    
                    # Send transcript event
                    await send_event(
                        TranscriptFinalEvent(
                            session_id=session_id,
                            speaker=speaker,
                            ts=ts,
                            text=text,
                            segment_id=segment_id,
                        )
                    )
                    
                    # Translate final text
                    context_entries = session.recent_context(
                        max_sentences=_HISTORY_CONTEXT_SENTENCES,
                        exclude_ts=ts,
                    )
                    recent_context = [
                        f"{entry.speaker}: {entry.text}" for entry in context_entries
                    ]
                    track_task(
                        asyncio.create_task(
                            translate_final_text(
                                text,
                                ts,
                                speaker,
                                recent_context,
                                segment_id,
                            )
                        )
                    )
                    
                    # Update suggestions if needed
                    if session.should_update_suggestions(False):
                        track_task(
                            asyncio.create_task(
                                generate_and_send_suggestions(
                                    session.recent_transcripts(),
                                    session.suggestions_prompt,
                                )
                            )
                        )
                except (WebSocketDisconnect, asyncio.CancelledError):
                    return
                except Exception:
                    logger.exception("Transcribe stream handling failed")
                    with contextlib.suppress(WebSocketDisconnect, RuntimeError):
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
    if correction_queue is not None:
        track_task(asyncio.create_task(process_corrections()))

    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if message.get("text") is not None:
                await _handle_control_message(message["text"], send_payload, session, transcribe_service)
                if _is_session_stop(message["text"]):
                    await send_event(SessionStopEvent())
                    is_closing = True
                    break
            elif message.get("bytes") is not None:
                await transcribe_service.send_audio(message["bytes"])
    except WebSocketDisconnect:
        is_closing = True
        return
    finally:
        is_closing = True
        log_event(
            logger,
            "ws.disconnected",
            session_id=session_id,
        )
        with contextlib.suppress(Exception):
            await transcribe_service.stop_stream()
        if background_tasks:
            for task in list(background_tasks):
                task.cancel()
            with contextlib.suppress(Exception):
                await asyncio.gather(*background_tasks, return_exceptions=True)
        try:
            await asyncio.wait_for(results_task, timeout=1.0)
        except asyncio.TimeoutError:
            results_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await results_task


async def _handle_control_message(
    raw_text: str,
    send_payload,
    session: MeetingSession,
    stt_service: STTServiceProtocol,
) -> None:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        await _send_invalid_message(send_payload, "Invalid JSON control message")
        return

    message_type = payload.get("type")
    if message_type == "client.ping":
        log_event(
            logger,
            "ws.ping",
            session_id=session.session_id,
            sample_rate=_LOG_SAMPLE_PING,
        )
        await send_payload({"type": "server.pong", "ts": epoch_ms()})
        return
    if message_type == "suggestions.prompt":
        prompt = payload.get("prompt", "")
        if not isinstance(prompt, str):
            await _send_invalid_message(send_payload, "Invalid suggestions prompt")
            return
        log_event(
            logger,
            "suggestions.prompt",
            session_id=session.session_id,
            text_len=len(prompt.strip()),
        )
        session.set_suggestions_prompt(prompt)
        return
    if message_type == "session.start":
        sample_rate = payload.get("sampleRate")
        if isinstance(sample_rate, int):
            stt_service.set_input_sample_rate(sample_rate)
            log_event(
                logger,
                "session.start",
                session_id=session.session_id,
                sample_rate=sample_rate,
            )
        return
    if message_type == "session.stop":
        log_event(
            logger,
            "session.stop",
            session_id=session.session_id,
        )
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
