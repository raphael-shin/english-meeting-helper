import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import Settings
from app.domain.models.session import TranscriptEntry
from app.services.suggestion import SuggestionService


@pytest.mark.asyncio
async def test_suggestion_generation_threshold() -> None:
    bedrock = SimpleNamespace(_invoke_model=AsyncMock(return_value="[]"))
    service = SuggestionService(bedrock, Settings())

    # Empty transcripts should return empty
    result = await service.generate_suggestions([])
    assert result == []
    bedrock._invoke_model.assert_not_called()

    response = json.dumps(
        [
            {"en": "Can you clarify the timeline?", "ko": "일정을 명확히 해주실 수 있나요?"},
            {"en": "Who owns the next action?", "ko": "다음 액션의 담당자는 누구인가요?"},
        ]
    )
    bedrock._invoke_model = AsyncMock(return_value=response)
    transcripts = [TranscriptEntry(speaker="spk", ts=1, text="Hello.")]

    result = await service.generate_suggestions(transcripts)
    assert 2 <= len(result) <= 5
