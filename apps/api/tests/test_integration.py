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
        return [
            {"en": "Can you clarify the owner?", "ko": "담당자를 명확히 해주실 수 있나요?"}
        ]


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


def _transcript_event(text: str, speaker: str) -> TranscriptResult:
    return TranscriptResult(is_partial=False, text=text, speaker=f"spk_{speaker}")


def test_integration_ws_flow(monkeypatch) -> None:
    async def transcript_stream() -> AsyncIterator[TranscriptResult]:
        yield _transcript_event("First sentence.", "1")
        yield _transcript_event("Second sentence.", "1")
        yield _transcript_event("Third sentence.", "2")

    _set_app_state()
    monkeypatch.setattr(
        meetings_module,
        "create_stt_service",
        lambda settings: make_stt_service(transcript_stream)(settings),
    )

    client = TestClient(app)
    with client.websocket_connect("/ws/v1/meetings/integration") as websocket:
        types = []
        websocket.send_text('{"type":"client.ping","ts":1}')
        for _ in range(20):
            message = websocket.receive_json()
            if message.get("type") == "server.pong":
                continue
            if message.get("type") == "display.update":
                continue
            types.append(message["type"])
            if message["type"] == "suggestions.update":
                break
        assert "transcript.final" in types
        assert "translation.final" in types
        assert "suggestions.update" in types


def test_integration_translate_api() -> None:
    _set_app_state()
    client = TestClient(app)
    response = client.post("/api/v1/translate/ko-en", json={"text": "안녕하세요"})
    assert response.status_code == 200
    assert response.json()["translatedText"] == "translated"
