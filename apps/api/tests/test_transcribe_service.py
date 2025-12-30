from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Settings
from app.services.stt.aws import AWSSTTService


class DummyStream:
    def __init__(self) -> None:
        self.input_stream = AsyncMock()
        self.output_stream = self._empty_stream()

    async def _empty_stream(self):
        if False:  # pragma: no cover
            yield {}


@pytest.mark.asyncio
@patch("app.services.stt.aws.TranscribeStreamingClient")
async def test_transcribe_service_stream_lifecycle(mock_client: AsyncMock) -> None:
    settings = Settings()
    stream = DummyStream()
    mock_client.return_value.start_stream_transcription = AsyncMock(return_value=stream)

    service = AWSSTTService(settings)
    await service.start_stream("session")

    mock_client.return_value.start_stream_transcription.assert_awaited_once()
    await service.send_audio(b"audio")
    stream.input_stream.send_audio_event.assert_awaited_once()

    await service.stop_stream()
    stream.input_stream.end_stream.assert_awaited_once()

    assert hasattr(service.get_results(), "__aiter__")
