from __future__ import annotations

from typing import AsyncIterator, Callable

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.ws import meetings as meetings_module


class FakeBedrockService:
    async def translate_en_to_ko(self, text: str) -> str:
        return "translated"


class FakeSuggestionService:
    async def generate_suggestions(  # type: ignore[no-untyped-def]
        self, transcripts, system_prompt=None
    ):
        return []


def make_transcribe_service(events: Callable[[], AsyncIterator[dict]]) -> type:
    class FakeTranscribeService:
        def __init__(self, settings: Settings) -> None:
            self._events = events

        async def start_stream(self, session_id: str) -> None:
            return None

        async def send_audio(self, audio_chunk: bytes) -> None:
            return None

        async def stop_stream(self) -> None:
            return None

        def get_results(self) -> AsyncIterator[dict]:
            return self._events()

    return FakeTranscribeService


def _set_app_state() -> None:
    app.state.settings = Settings()
    app.state.bedrock_service = FakeBedrockService()
    app.state.suggestion_service = FakeSuggestionService()


def test_ws_emits_transcript_events(monkeypatch) -> None:
    async def transcript_stream() -> AsyncIterator[dict]:
        yield {
            "Transcript": {
                "Results": [
                    {
                        "IsPartial": True,
                        "Alternatives": [
                            {"Transcript": "Hello", "Items": [{"Speaker": "1"}]}
                        ],
                    }
                ]
            }
        }
        yield {
            "Transcript": {
                "Results": [
                    {
                        "IsPartial": False,
                        "Alternatives": [
                            {"Transcript": "Hello world.", "Items": [{"Speaker": "1"}]}
                        ],
                    }
                ]
            }
        }

    _set_app_state()
    monkeypatch.setattr(meetings_module, "TranscribeService", make_transcribe_service(transcript_stream))

    client = TestClient(app)
    with client.websocket_connect("/ws/v1/meetings/test-session") as websocket:
        websocket.send_text('{"type":"client.ping","ts":1}')
        pong = websocket.receive_json()
        if pong.get("type") != "server.pong":
            first = pong
        else:
            first = websocket.receive_json()
        second = websocket.receive_json()
        assert first["type"] == "transcript.partial"
        assert second["type"] == "transcript.final"


def test_ws_emits_translation_after_final(monkeypatch) -> None:
    async def transcript_stream() -> AsyncIterator[dict]:
        yield {
            "Transcript": {
                "Results": [
                    {
                        "IsPartial": False,
                        "Alternatives": [
                            {"Transcript": "Hello world.", "Items": [{"Speaker": "1"}]}
                        ],
                    }
                ]
            }
        }

    _set_app_state()
    monkeypatch.setattr(meetings_module, "TranscribeService", make_transcribe_service(transcript_stream))

    client = TestClient(app)
    with client.websocket_connect("/ws/v1/meetings/test-session") as websocket:
        websocket.send_text('{"type":"client.ping","ts":1}')
        pong = websocket.receive_json()
        if pong.get("type") != "server.pong":
            first = pong
        else:
            first = websocket.receive_json()
        second = websocket.receive_json()
        assert first["type"] == "transcript.final"
        assert second["type"] == "translation.final"


def test_ws_invalid_message_returns_error(monkeypatch) -> None:
    async def empty_stream() -> AsyncIterator[dict]:
        if False:  # pragma: no cover
            yield {}

    _set_app_state()
    monkeypatch.setattr(meetings_module, "TranscribeService", make_transcribe_service(empty_stream))

    client = TestClient(app)
    with client.websocket_connect("/ws/v1/meetings/test-session") as websocket:
        websocket.send_text("not-json")
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert response["code"] == "INVALID_MESSAGE"
