from __future__ import annotations

import asyncio
import contextlib
from typing import Any, AsyncIterator

try:
    from amazon_transcribe.client import TranscribeStreamingClient
except ModuleNotFoundError:  # pragma: no cover - optional dependency in local dev
    TranscribeStreamingClient = None

from app.core.config import Settings
from app.domain.models.provider import TranscriptResult


class AWSSTTService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if TranscribeStreamingClient is None:
            raise RuntimeError("amazon-transcribe is required for AWSSTTService")
        self.client = TranscribeStreamingClient(region=settings.aws_region)
        self._stream = None
        self._results_queue: asyncio.Queue[TranscriptResult] = asyncio.Queue()
        self._results_task: asyncio.Task | None = None
        self._input_sample_rate = settings.transcribe_sample_rate

    async def start_stream(self, session_id: str) -> None:
        self._stream = await self.client.start_stream_transcription(
            language_code=self.settings.transcribe_language_code,
            media_sample_rate_hz=self.settings.transcribe_sample_rate,
            media_encoding=self.settings.transcribe_media_encoding,
            show_speaker_label=True,
            enable_partial_results_stabilization=True,
            partial_results_stability="high",
        )
        self._results_task = asyncio.create_task(self._process_results())

    async def send_audio(self, audio_chunk: bytes) -> None:
        if self._stream is None:
            return
        await self._stream.input_stream.send_audio_event(audio_chunk=audio_chunk)

    async def stop_stream(self) -> None:
        if self._stream is None:
            return
        await self._stream.input_stream.end_stream()
        if self._results_task:
            try:
                await asyncio.wait_for(self._results_task, timeout=1.0)
            except asyncio.TimeoutError:
                self._results_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._results_task

    def set_input_sample_rate(self, sample_rate: int) -> None:
        self._input_sample_rate = sample_rate

    async def _process_results(self) -> None:
        if self._stream is None:
            return
        try:
            async for event in self._stream.output_stream:
                for is_partial, speaker, text in _parse_transcribe_event(event):
                    await self._results_queue.put(
                        TranscriptResult(is_partial=is_partial, text=text, speaker=speaker)
                    )
        except asyncio.CancelledError:
            return

    async def get_results(self) -> AsyncIterator[TranscriptResult]:
        while True:
            result = await self._results_queue.get()
            yield result


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
