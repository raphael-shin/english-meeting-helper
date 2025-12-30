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
    assert service._invoke_model.call_args.args[0] == settings.bedrock_translation_model_id
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
