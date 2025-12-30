from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import struct
from typing import AsyncIterator

import websockets
from websockets.exceptions import ConnectionClosed

from app.core.config import Settings
from app.domain.models.provider import TranscriptResult
from app.services.stt import get_openai_language_code


class OpenAISTTService:
    REALTIME_API_URL = "wss://api.openai.com/v1/realtime"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._results_queue: asyncio.Queue[TranscriptResult | None] = asyncio.Queue()
        self._receive_task: asyncio.Task | None = None
        self._running = False
        self._partial_by_item: dict[str, str] = {}
        self._last_commit_ts: float = 0.0
        self._input_sample_rate = 24000
        self._stream_error: Exception | None = None

    async def start_stream(self, session_id: str) -> None:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI STT")

        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "OpenAI-Beta": "realtime=v1",
        }
        self._ws = await websockets.connect(
            f"{self.REALTIME_API_URL}?model={self.settings.openai_stt_model}",
            extra_headers=headers,
        )

        language = self.settings.openai_stt_language or get_openai_language_code(
            self.settings.transcribe_language_code
        )
        await self._ws.send(
            json.dumps(
                {
                    "type": "session.update",
                    "session": {
                        "type": "transcription",
                        "audio": {
                            "input": {
                                "format": {"type": "audio/pcm", "rate": 24000},
                                "transcription": {
                                    "model": self.settings.openai_stt_model,
                                    "language": language,
                                },
                                "turn_detection": None,
                            }
                        },
                    },
                }
            )
        )

        self._running = True
        self._receive_task = asyncio.create_task(self._receive_loop())

    async def send_audio(self, audio_chunk: bytes) -> None:
        if not self._ws:
            return
        resampled = audio_chunk
        if self._input_sample_rate != 24000:
            resampled = self._resample_16k_to_24k(audio_chunk)
        audio_b64 = base64.b64encode(resampled).decode()
        await self._ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": audio_b64}))
        await self._maybe_commit_buffer()

    async def stop_stream(self) -> None:
        self._running = False
        if self._receive_task:
            self._receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._receive_task
        if self._ws:
            await self._ws.close()

    def set_input_sample_rate(self, sample_rate: int) -> None:
        self._input_sample_rate = sample_rate

    async def get_results(self) -> AsyncIterator[TranscriptResult]:
        while self._running or not self._results_queue.empty():
            if self._stream_error:
                raise self._stream_error
            try:
                result = await asyncio.wait_for(self._results_queue.get(), timeout=0.1)
                if result is None:
                    if self._stream_error:
                        raise self._stream_error
                    continue
                yield result
            except asyncio.TimeoutError:
                continue

    async def _maybe_commit_buffer(self) -> None:
        now = asyncio.get_running_loop().time()
        if now - self._last_commit_ts < self.settings.openai_commit_interval_ms / 1000:
            return
        self._last_commit_ts = now
        if self._ws:
            await self._ws.send(json.dumps({"type": "input_audio_buffer.commit"}))

    def _resample_16k_to_24k(self, audio_16k: bytes) -> bytes:
        samples_16k = struct.unpack(f"<{len(audio_16k)//2}h", audio_16k)
        if not samples_16k:
            return b""
        out_len = int(len(samples_16k) * 3 / 2)
        samples_24k = []
        for j in range(out_len):
            pos = j * 2 / 3
            i = int(pos)
            frac = pos - i
            left = samples_16k[i]
            right = samples_16k[i + 1] if i + 1 < len(samples_16k) else samples_16k[i]
            sample = int(left * (1 - frac) + right * frac)
            samples_24k.append(sample)
        return struct.pack(f"<{len(samples_24k)}h", *samples_24k)

    async def _receive_loop(self) -> None:
        while self._running and self._ws:
            try:
                msg = await self._ws.recv()
                data = json.loads(msg)
            except (ConnectionClosed, json.JSONDecodeError) as exc:
                await self._signal_error(exc)
                break

            event_type = data.get("type")
            if event_type == "conversation.item.input_audio_transcription.delta":
                item_id = data.get("item_id", "")
                delta = data.get("delta") or ""
                if item_id:
                    self._partial_by_item[item_id] = self._partial_by_item.get(item_id, "") + delta
                    await self._results_queue.put(
                        TranscriptResult(
                            is_partial=True,
                            text=self._partial_by_item[item_id],
                            speaker="spk_1",
                        )
                    )
            elif event_type == "conversation.item.input_audio_transcription.completed":
                item_id = data.get("item_id", "")
                transcript = data.get("transcript") or ""
                if item_id:
                    self._partial_by_item.pop(item_id, None)
                await self._results_queue.put(
                    TranscriptResult(is_partial=False, text=transcript, speaker="spk_1")
                )
            elif event_type == "conversation.item.input_audio_transcription.failed":
                await self._signal_error(RuntimeError("OpenAI transcription failed"))
                break

    async def _signal_error(self, exc: Exception) -> None:
        if self._stream_error is None:
            self._stream_error = exc
        self._running = False
        await self._results_queue.put(None)
