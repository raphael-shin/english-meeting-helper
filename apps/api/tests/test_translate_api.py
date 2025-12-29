from fastapi.testclient import TestClient

from app.core.deps import get_bedrock_service
from app.main import app


class FakeBedrockService:
    async def translate_ko_to_en(self, text: str) -> str:
        return "translated"


def test_translate_empty_input_returns_400() -> None:
    app.dependency_overrides[get_bedrock_service] = lambda: FakeBedrockService()
    client = TestClient(app)
    response = client.post("/api/v1/translate/ko-en", json={"text": "   "})
    assert response.status_code == 400
    app.dependency_overrides.clear()


def test_translate_success() -> None:
    app.dependency_overrides[get_bedrock_service] = lambda: FakeBedrockService()
    client = TestClient(app)
    response = client.post("/api/v1/translate/ko-en", json={"text": "안녕하세요"})
    assert response.status_code == 200
    assert response.json()["translatedText"] == "translated"
    app.dependency_overrides.clear()
