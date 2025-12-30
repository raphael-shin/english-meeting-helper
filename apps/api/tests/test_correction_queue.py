import asyncio

from app.domain.models.subtitle import SubtitleSegment
from app.services.correction import CorrectionQueue


class DummyBedrock:
    async def invoke_correction(self, prompt: str) -> str:
        return prompt


def _segment(segment_id: int, text: str) -> SubtitleSegment:
    return SubtitleSegment(
        id=f"seg_{segment_id}",
        text=text,
        speaker="spk_1",
        start_time=0,
        end_time=1,
        is_final=True,
        llm_corrected=False,
        segment_id=segment_id,
    )


def test_parse_corrections_returns_changes() -> None:
    queue = CorrectionQueue(DummyBedrock(), batch_size=2)
    segments = [_segment(1, "Hello wrld"), _segment(2, "All good")]
    response = '{"corrections": ["Hello world", "All good"]}'
    corrections = queue._parse_corrections(response, segments)
    assert corrections == [(1, "Hello wrld", "Hello world")]


def test_parse_corrections_ignores_invalid_json() -> None:
    queue = CorrectionQueue(DummyBedrock(), batch_size=2)
    segments = [_segment(1, "Hello")]
    corrections = queue._parse_corrections("not json", segments)
    assert corrections == []


def test_process_batch_empty_queue() -> None:
    queue = CorrectionQueue(DummyBedrock(), batch_size=2)
    corrections = asyncio.run(queue.process_batch())
    assert corrections == []
