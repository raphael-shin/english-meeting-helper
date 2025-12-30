from app.domain.models.session import MeetingSession
from app.domain.models.subtitle import SubtitleSegment


def test_display_buffer_fifo_and_current_clear() -> None:
    session = MeetingSession("sess")

    current_segment = SubtitleSegment(
        id="seg_1",
        text="Partial text",
        speaker="spk_1",
        start_time=100,
        end_time=None,
        is_final=False,
        llm_corrected=False,
        segment_id=1,
    )
    buffer = session.update_display_buffer(current_segment)
    assert buffer.current is not None
    assert buffer.current.segment_id == 1

    for index in range(1, 6):
        final_segment = SubtitleSegment(
            id=f"seg_{index}",
            text=f"Final {index}",
            speaker="spk_1",
            start_time=100 + index,
            end_time=110 + index,
            is_final=True,
            llm_corrected=False,
            segment_id=index,
        )
        buffer = session.update_display_buffer(final_segment)

    assert buffer.current is None
    assert len(buffer.confirmed) == 4
    assert [segment.segment_id for segment in buffer.confirmed] == [2, 3, 4, 5]
