from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
import pytest
from hypothesis import given, strategies as st

from app.main import app
from app.ws import meetings as meetings_module
from app.domain.models.provider import TranscriptResult


@pytest.mark.asyncio
async def test_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


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


def test_ws_meetings_ping_pong(monkeypatch) -> None:
    async def empty_stream():
        if False:  # pragma: no cover
            yield TranscriptResult(is_partial=True, text="", speaker="spk_1")

    class FakeSTTService:
        async def start_stream(self, session_id: str) -> None:
            return None

        async def send_audio(self, audio_chunk: bytes) -> None:
            return None

        async def stop_stream(self) -> None:
            return None

        def set_input_sample_rate(self, sample_rate: int) -> None:
            return None

        def get_results(self):
            return empty_stream()

    app.state.translation_service = FakeTranslationService()
    app.state.bedrock_service = FakeTranslationService()
    app.state.suggestion_service = FakeSuggestionService()
    monkeypatch.setattr(meetings_module, "create_stt_service", lambda settings: FakeSTTService())
    client = TestClient(app)
    with client.websocket_connect("/ws/v1/meetings/test-session") as websocket:
        websocket.send_text('{"type":"client.ping","ts":123}')
        response = websocket.receive_json()
        assert response["type"] == "server.pong"


@given(
    st.dictionaries(
        keys=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=6),
        values=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), max_size=12),
        max_size=3,
    )
)
def test_health_endpoint_consistency(params: dict[str, str]) -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health", params=params)
    assert response.status_code == 200
    assert response.json().get("status") == "ok"
