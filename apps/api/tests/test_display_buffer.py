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


def test_display_buffer_partial_translation_update() -> None:
    """Test that partial segment translation can be updated progressively."""
    session = MeetingSession("sess")

    # Add partial segment without translation
    partial_segment = SubtitleSegment(
        id="seg_1",
        text="Hello world",
        speaker="spk_1",
        start_time=100,
        end_time=None,
        is_final=False,
        llm_corrected=False,
        segment_id=1,
        translation=None,
    )
    buffer = session.update_display_buffer(partial_segment)
    assert buffer.current is not None
    assert buffer.current.translation is None

    # Update with translation (simulating async translation completion)
    buffer.current.translation = "안녕하세요"
    assert buffer.current.translation == "안녕하세요"
    assert buffer.current.segment_id == 1


def test_display_buffer_confirmed_with_translation() -> None:
    """Test that confirmed segments include translation."""
    session = MeetingSession("sess")

    final_segment = SubtitleSegment(
        id="seg_1",
        text="Good morning",
        speaker="spk_1",
        start_time=100,
        end_time=200,
        is_final=True,
        llm_corrected=False,
        segment_id=1,
        translation="좋은 아침입니다",
    )
    buffer = session.update_display_buffer(final_segment)
    
    assert len(buffer.confirmed) == 1
    assert buffer.confirmed[0].translation == "좋은 아침입니다"
    assert buffer.confirmed[0].text == "Good morning"
