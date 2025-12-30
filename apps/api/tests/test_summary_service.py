from types import SimpleNamespace
from unittest.mock import AsyncMock

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
async def test_summary_parses_json_response() -> None:
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
async def test_summary_normalizes_string_lists() -> None:
    raw_markdown = "## 5줄 요약\n- 요약 1\n- 요약 2\n- 요약 3\n- 요약 4\n- 요약 5\n"
    bedrock = SimpleNamespace(_invoke_model=AsyncMock(return_value=raw_markdown))
    service = SummaryService(bedrock, Settings())

    transcripts = [TranscriptEntry(speaker="spk_1", ts=1, text="We reviewed risks.")]
    result = await service.generate_summary(transcripts)

    assert result == raw_markdown.strip()
