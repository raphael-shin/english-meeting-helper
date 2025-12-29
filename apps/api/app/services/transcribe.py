from __future__ import annotations

from typing import AsyncIterator, Protocol

try:
    from amazon_transcribe.client import TranscribeStreamingClient
    from amazon_transcribe.model import TranscriptEvent
except ModuleNotFoundError:  # pragma: no cover - optional dependency in local dev
    TranscribeStreamingClient = None

    class TranscriptEvent:  # type: ignore[no-redef]
        pass

from app.core.config import Settings


class TranscribeServiceProtocol(Protocol):
    async def start_stream(self, session_id: str) -> None: ...

    async def send_audio(self, audio_chunk: bytes) -> None: ...

    async def stop_stream(self) -> None: ...

    def get_results(self) -> AsyncIterator[TranscriptEvent]: ...


class TranscribeService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if TranscribeStreamingClient is None:
            raise RuntimeError("amazon-transcribe is required for TranscribeService")
        self.client = TranscribeStreamingClient(region=settings.aws_region)
        self._stream = None

    async def start_stream(self, session_id: str) -> None:
        self._stream = await self.client.start_stream_transcription(
            language_code=self.settings.transcribe_language_code,
            media_sample_rate_hz=self.settings.transcribe_sample_rate,
            media_encoding=self.settings.transcribe_media_encoding,
        )

    async def send_audio(self, audio_chunk: bytes) -> None:
        if self._stream is None:
            return
        await self._stream.input_stream.send_audio_event(audio_chunk=audio_chunk)

    async def stop_stream(self) -> None:
        if self._stream is None:
            return
        await self._stream.input_stream.end_stream()

    def get_results(self) -> AsyncIterator[TranscriptEvent]:
        if self._stream is None:
            raise RuntimeError("Transcribe stream not started")
        return self._stream.output_stream
