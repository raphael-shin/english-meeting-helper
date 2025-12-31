from types import SimpleNamespace
from unittest.mock import AsyncMock, ANY

import pytest

from app.core.config import Settings
from app.domain.models.session import TranscriptEntry
from app.services.summary import SummaryService


@pytest.mark.asyncio
async def test_summary_empty_transcripts_returns_none() -> None:
    bedrock = SimpleNamespace(_invoke_model=AsyncMock(return_value=""))
    service = SummaryService(bedrock, Settings())

    result = await service.generate_summary([])
    assert result is None
    bedrock._invoke_model.assert_not_called()


@pytest.mark.asyncio
async def test_summary_returns_markdown() -> None:
    markdown = (
        "## 5줄 요약\n"
        "- 요약 1\n"
        "- 요약 2\n"
        "- 요약 3\n"
        "- 요약 4\n"
        "- 요약 5\n"
        "\n"
        "## 핵심 내용\n"
        "- 핵심 1\n"
        "- 핵심 2\n"
        "\n"
        "## Action Items\n"
        "- 액션 1\n"
    )
    bedrock = SimpleNamespace(_invoke_model=AsyncMock(return_value=markdown))
    service = SummaryService(bedrock, Settings())

    transcripts = [TranscriptEntry(speaker="spk_1", ts=1, text="We decided on scope.")]
    result = await service.generate_summary(transcripts)

    assert result == markdown.strip()


@pytest.mark.asyncio
async def test_summary_trims_markdown() -> None:
    raw_markdown = "## 5줄 요약\n- 요약 1\n- 요약 2\n- 요약 3\n- 요약 4\n- 요약 5\n"
    bedrock = SimpleNamespace(_invoke_model=AsyncMock(return_value=raw_markdown))
    service = SummaryService(bedrock, Settings())

    transcripts = [TranscriptEntry(speaker="spk_1", ts=1, text="We reviewed risks.")]
    result = await service.generate_summary(transcripts)

    assert result == raw_markdown.strip()


@pytest.mark.asyncio
async def test_context_trimming() -> None:
    bedrock = SimpleNamespace(_invoke_model=AsyncMock(return_value="Summary"))
    service = SummaryService(bedrock, Settings())
    service.max_context_chars = 20  # Mock small limit

    transcripts = [
        TranscriptEntry(speaker="spk_1", ts=1, text="Old message"),     # 12 chars
        TranscriptEntry(speaker="spk_1", ts=2, text="Recent msg"),      # 11 chars
    ]
    # "spk_1: Recent msg" is 17 chars.
    # "spk_1: Old message" is 18 chars.
    # Total would be 35 chars. Limit is 20.
    # Should keep only the last one.

    await service.generate_summary(transcripts)

    call_args = bedrock._invoke_model.call_args
    prompt_sent = call_args[0][1]
    
    assert "spk_1: Recent msg" in prompt_sent
    assert "spk_1: Old message" not in prompt_sent


@pytest.mark.asyncio
async def test_model_selection_fallback() -> None:
    # Case 1: High model ID is present
    bedrock = SimpleNamespace(_invoke_model=AsyncMock(return_value="Summary"))
    settings = Settings()
    settings.bedrock_translation_high_model_id = "high-model"
    settings.bedrock_translation_fast_model_id = "fast-model"
    
    service = SummaryService(bedrock, settings)
    
    await service.generate_summary([TranscriptEntry(speaker="spk", ts=1, text="text")])
    bedrock._invoke_model.assert_called_with("high-model", ANY)

    # Case 2: High model ID is missing (fallback)
    bedrock._invoke_model.reset_mock()
    settings = Settings()
    settings.bedrock_translation_high_model_id = ""  # Empty
    settings.bedrock_translation_fast_model_id = "fast-model"
    
    service = SummaryService(bedrock, settings)
    
    await service.generate_summary([TranscriptEntry(speaker="spk", ts=1, text="text")])
    bedrock._invoke_model.assert_called_with("fast-model", ANY)
