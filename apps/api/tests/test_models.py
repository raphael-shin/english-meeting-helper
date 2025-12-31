import re

from hypothesis import given, strategies as st

from app.domain.models.events import (
    ErrorEvent,
    SessionStartEvent,
    SessionStopEvent,
    SuggestionItem,
    SuggestionsUpdateEvent,
    SummaryUpdateEvent,
    TranscriptCorrectedEvent,
    TranscriptFinalEvent,
    TranscriptPartialEvent,
    TranslationCorrectedEvent,
    TranslationFinalEvent,
)
from app.domain.models.session import MeetingSession


@given(
    session_id=st.text(min_size=1, max_size=12),
    speaker=st.text(min_size=1, max_size=8),
    text=st.text(min_size=1, max_size=40),
)
def test_event_structure_transcript_events(session_id: str, speaker: str, text: str) -> None:
    partial = TranscriptPartialEvent(
        session_id=session_id,
        speaker=speaker,
        text=text,
        segment_id=1,
    )
    final = TranscriptFinalEvent(
        session_id=session_id,
        speaker=speaker,
        text=text,
        segment_id=2,
    )

    for event, expected_type in [
        (partial, "transcript.partial"),
        (final, "transcript.final"),
    ]:
        payload = event.model_dump(by_alias=True)
        assert payload["type"] == expected_type
        assert "ts" in payload
        assert payload["sessionId"] == session_id
        assert payload["speaker"] == speaker
        assert payload["text"] == text
        assert "segmentId" in payload


def test_event_structure_control_and_error() -> None:
    start = SessionStartEvent(sample_rate=16000, format="pcm_s16le", lang="en-US")
    stop = SessionStopEvent()
    error = ErrorEvent(code="INVALID_MESSAGE", message="bad input", retryable=False)

    start_payload = start.model_dump(by_alias=True)
    stop_payload = stop.model_dump(by_alias=True)
    error_payload = error.model_dump(by_alias=True)

    assert start_payload["type"] == "session.start"
    assert start_payload["sampleRate"] == 16000
    assert start_payload["format"] == "pcm_s16le"
    assert start_payload["lang"] == "en-US"
    assert "ts" in start_payload

    assert stop_payload["type"] == "session.stop"
    assert "ts" in stop_payload

    assert error_payload["type"] == "error"
    assert error_payload["code"] == "INVALID_MESSAGE"
    assert error_payload["message"] == "bad input"
    assert error_payload["retryable"] is False


@given(
    session_id=st.text(min_size=1, max_size=12),
    speaker=st.text(min_size=1, max_size=8),
    text=st.text(min_size=1, max_size=40),
    translated=st.text(min_size=1, max_size=40),
)
def test_event_structure_translation(session_id: str, speaker: str, text: str, translated: str) -> None:
    event = TranslationFinalEvent(
        session_id=session_id,
        source_ts=123,
        segment_id=5,
        speaker=speaker,
        source_text=text,
        translated_text=translated,
    )
    payload = event.model_dump(by_alias=True)
    assert payload["type"] == "translation.final"
    assert payload["sessionId"] == session_id
    assert payload["sourceTs"] == 123
    assert payload["segmentId"] == 5
    assert payload["sourceText"] == text
    assert payload["translatedText"] == translated
    assert payload["speaker"] == speaker


def test_event_structure_corrections() -> None:
    transcript_event = TranscriptCorrectedEvent(
        session_id="sess",
        segment_id=1,
        original_text="orig",
        corrected_text="fixed",
    )
    translation_event = TranslationCorrectedEvent(
        session_id="sess",
        segment_id=2,
        speaker="spk_1",
        source_text="fixed",
        translated_text="고침",
    )

    transcript_payload = transcript_event.model_dump(by_alias=True)
    translation_payload = translation_event.model_dump(by_alias=True)

    assert transcript_payload["type"] == "transcript.corrected"
    assert transcript_payload["segmentId"] == 1
    assert transcript_payload["originalText"] == "orig"
    assert transcript_payload["correctedText"] == "fixed"

    assert translation_payload["type"] == "translation.corrected"
    assert translation_payload["segmentId"] == 2
    assert translation_payload["speaker"] == "spk_1"
    assert translation_payload["sourceText"] == "fixed"
    assert translation_payload["translatedText"] == "고침"


def test_event_structure_suggestions() -> None:
    items = [SuggestionItem(en="Question?", ko="질문?")]
    event = SuggestionsUpdateEvent(session_id="sess", items=items)
    payload = event.model_dump(by_alias=True)
    assert payload["type"] == "suggestions.update"
    assert payload["sessionId"] == "sess"
    assert payload["items"][0]["en"] == "Question?"
    assert payload["items"][0]["ko"] == "질문?"


def test_event_structure_summary() -> None:
    markdown = "## 5줄 요약\n- 요약 1\n- 요약 2\n- 요약 3\n- 요약 4\n- 요약 5"
    event = SummaryUpdateEvent(session_id="sess", summary_markdown=markdown)
    payload = event.model_dump(by_alias=True)
    assert payload["type"] == "summary.update"
    assert payload["sessionId"] == "sess"
    assert payload["summaryMarkdown"] == markdown


@given(
    sentences=st.lists(
        st.text(
            min_size=1,
            max_size=10,
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
        ),
        min_size=1,
        max_size=6,
    )
)
def test_sentence_boundary_detection(sentences: list[str]) -> None:
    """Final transcript는 더 이상 분할하지 않음 - 단일 segment로 처리"""
    session = MeetingSession("sess")
    text = ". ".join(sentence.strip() for sentence in sentences) + "."
    result_text, segment_id = session.add_final_transcript("spk", text, 100)
    assert result_text == text
    assert segment_id is not None


def test_sentence_boundary_buffering_across_transcripts() -> None:
    """Final transcript는 그대로 저장됨 - buffering 없음"""
    session = MeetingSession("sess")
    text1, seg_id1 = session.add_final_transcript("spk", "This is incomplete", 100)
    assert text1 == "This is incomplete"
    assert seg_id1 is not None
    
    text2, seg_id2 = session.add_final_transcript("spk", "but now complete.", 200)
    assert text2 == "but now complete."
    assert seg_id2 is not None


def test_buffer_flushes_on_speaker_change() -> None:
    session = MeetingSession("sess")
    text1, seg_id1 = session.add_final_transcript("spk_1", "This is incomplete", 100)
    assert text1 == "This is incomplete"
    
    text2, seg_id2 = session.add_final_transcript("spk_2", "Hello.", 200)
    assert text2 == "Hello."
    assert seg_id2 != seg_id1


def test_session_state_accumulation() -> None:
    session = MeetingSession("sess")
    text, segment_id = session.add_final_transcript("spk", "Hello.", 100)
    assert text == "Hello."
    assert segment_id is not None
    
    session.add_translation("spk", 100, "Hello.", "안녕하세요.")
    assert len(session.transcripts) == 1
    assert len(session.translations) == 1
