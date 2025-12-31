from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Settings
from app.services.translation.aws import AWSTranslationService


@pytest.mark.asyncio
@patch("app.services.translation.aws.boto3.client")
async def test_translate_en_to_ko_uses_translation_model(mock_client: AsyncMock) -> None:
    settings = Settings()
    service = AWSTranslationService(settings)
    service._invoke_model = AsyncMock(return_value="translated")

    result = await service.translate_en_to_ko("Hello")

    service._invoke_model.assert_awaited_once()
    assert service._invoke_model.call_args.args[0] == settings.bedrock_translation_fast_model_id
    assert "Translate the following English text" in service._invoke_model.call_args.args[1]
    assert result == "translated"


@pytest.mark.asyncio
@patch("app.services.translation.aws.boto3.client")
async def test_translate_ko_to_en_uses_quick_model(mock_client: AsyncMock) -> None:
    settings = Settings()
    service = AWSTranslationService(settings)
    service._invoke_model = AsyncMock(return_value="translated")

    result = await service.translate_ko_to_en("안녕하세요")

    service._invoke_model.assert_awaited_once()
    assert service._invoke_model.call_args.args[0] == settings.bedrock_quick_translate_model_id
    assert "Translate the following Korean text" in service._invoke_model.call_args.args[1]
    assert result == "translated"


@pytest.mark.asyncio
@patch("app.services.translation.aws.boto3.client")
async def test_translate_en_to_ko_history_uses_high_model(mock_client: AsyncMock) -> None:
    settings = Settings()
    settings.bedrock_translation_high_model_id = "high-model"
    settings.bedrock_translation_fast_model_id = "fast-model"
    service = AWSTranslationService(settings)
    service._invoke_model = AsyncMock(return_value="translated_history")

    result = await service.translate_en_to_ko_history(
        "Hello there",
        recent_context=["Earlier line", "Another line"],
    )

    service._invoke_model.assert_awaited_once()
    assert service._invoke_model.call_args.args[0] == "high-model"
    prompt = service._invoke_model.call_args.args[1]
    assert "Recent context:" in prompt
    assert "- Earlier line" in prompt
    assert "- Another line" in prompt
    assert "Current line" in prompt
    assert result == "translated_history"


@pytest.mark.asyncio
@patch("app.services.translation.aws.boto3.client")
async def test_translate_for_display_includes_confirmed_context(mock_client: AsyncMock) -> None:
    settings = Settings()
    settings.bedrock_translation_high_model_id = "high-model"
    service = AWSTranslationService(settings)
    service._invoke_model = AsyncMock(return_value="display")

    result = await service.translate_for_display(
        "We should proceed.",
        confirmed_texts=["First confirmed", "Second confirmed"],
    )

    service._invoke_model.assert_awaited_once()
    assert service._invoke_model.call_args.args[0] == "high-model"
    prompt = service._invoke_model.call_args.args[1]
    assert "Confirmed context" in prompt
    assert "- First confirmed" in prompt
    assert "- Second confirmed" in prompt
    assert "Current sentence" in prompt
    assert result == "display"


@pytest.mark.asyncio
@patch("app.services.translation.aws.boto3.client")
async def test_invoke_correction_uses_correction_model(mock_client: AsyncMock) -> None:
    settings = Settings()
    settings.bedrock_correction_model_id = "correction-model"
    service = AWSTranslationService(settings)
    service._invoke_model = AsyncMock(return_value="fixed")

    result = await service.invoke_correction("Fix this line.")

    service._invoke_model.assert_awaited_once()
    assert service._invoke_model.call_args.args[0] == "correction-model"
    assert "Fix this line." in service._invoke_model.call_args.args[1]
    assert result == "fixed"
