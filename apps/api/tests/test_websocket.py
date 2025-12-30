from __future__ import annotations

from typing import AsyncIterator, Callable

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.ws import meetings as meetings_module
from app.domain.models.provider import TranscriptResult


class FakeTranslationService:
    async def translate_en_to_ko(self, text: str) -> str:
        return "translated"

    async def translate_en_to_ko_history(
        self, text: str, recent_context: list[str] | None = None
    ) -> str:
        return "translated_history"

    async def translate_ko_to_en(self, text: str) -> str:
        return "translated"


class FakeSuggestionService:
    async def generate_suggestions(  # type: ignore[no-untyped-def]
        self, transcripts, system_prompt=None
    ):
        return []


def make_stt_service(events: Callable[[], AsyncIterator[TranscriptResult]]) -> type:
    class FakeSTTService:
        def __init__(self, settings: Settings) -> None:
            self._events = events

        async def start_stream(self, session_id: str) -> None:
            return None

        async def send_audio(self, audio_chunk: bytes) -> None:
            return None

        async def stop_stream(self) -> None:
            return None

        def set_input_sample_rate(self, sample_rate: int) -> None:
            return None

        def get_results(self) -> AsyncIterator[TranscriptResult]:
            return self._events()

    return FakeSTTService


def _set_app_state() -> None:
    app.state.settings = Settings()
    app.state.translation_service = FakeTranslationService()
    app.state.bedrock_service = FakeTranslationService()
    app.state.suggestion_service = FakeSuggestionService()


def test_ws_emits_transcript_events(monkeypatch) -> None:
    async def transcript_stream() -> AsyncIterator[TranscriptResult]:
        yield TranscriptResult(
            is_partial=True,
            text="Hello this is a partial update",
            speaker="spk_1",
        )
        yield TranscriptResult(is_partial=False, text="Hello world.", speaker="spk_1")

    _set_app_state()
    monkeypatch.setattr(meetings_module, "create_stt_service", lambda settings: make_stt_service(transcript_stream)(settings))

    client = TestClient(app)
    with client.websocket_connect("/ws/v1/meetings/test-session") as websocket:
        types = []
        for index in range(10):
            websocket.send_text(f'{{"type":"client.ping","ts":{index}}}')
            message = websocket.receive_json()
            if message.get("type") == "server.pong":
                continue
            if message.get("type") == "display.update":
                continue
            types.append(message["type"])
            if "transcript.partial" in types and "transcript.final" in types:
                break
        assert "transcript.partial" in types
        assert "transcript.final" in types


def test_ws_emits_translation_after_final(monkeypatch) -> None:
    async def transcript_stream() -> AsyncIterator[TranscriptResult]:
        yield TranscriptResult(is_partial=False, text="Hello world.", speaker="spk_1")

    _set_app_state()
    monkeypatch.setattr(meetings_module, "create_stt_service", lambda settings: make_stt_service(transcript_stream)(settings))

    client = TestClient(app)
    with client.websocket_connect("/ws/v1/meetings/test-session") as websocket:
        types = []
        for index in range(10):
            websocket.send_text(f'{{"type":"client.ping","ts":{index}}}')
            message = websocket.receive_json()
            if message.get("type") == "server.pong":
                continue
            if message.get("type") == "display.update":
                continue
            types.append(message["type"])
            if "transcript.final" in types and "translation.final" in types:
                break
        assert "transcript.final" in types
        assert "translation.final" in types


def test_ws_invalid_message_returns_error(monkeypatch) -> None:
    async def empty_stream() -> AsyncIterator[TranscriptResult]:
        if False:  # pragma: no cover
            yield TranscriptResult(is_partial=True, text="", speaker="spk_1")

    _set_app_state()
    monkeypatch.setattr(meetings_module, "create_stt_service", lambda settings: make_stt_service(empty_stream)(settings))

    client = TestClient(app)
    with client.websocket_connect("/ws/v1/meetings/test-session") as websocket:
        websocket.send_text("not-json")
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert response["code"] == "INVALID_MESSAGE"
