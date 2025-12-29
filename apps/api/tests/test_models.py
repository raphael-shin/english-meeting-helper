import re

from hypothesis import given, strategies as st

from app.domain.models.events import (
    ErrorEvent,
    SessionStartEvent,
    SessionStopEvent,
    SuggestionItem,
    SuggestionsUpdateEvent,
    TranscriptFinalEvent,
    TranscriptPartialEvent,
    TranslationFinalEvent,
)
from app.domain.models.session import MeetingSession


@given(
    session_id=st.text(min_size=1, max_size=12),
    speaker=st.text(min_size=1, max_size=8),
    text=st.text(min_size=1, max_size=40),
)
def test_event_structure_transcript_events(session_id: str, speaker: str, text: str) -> None:
    partial = TranscriptPartialEvent(session_id=session_id, speaker=speaker, text=text)
    final = TranscriptFinalEvent(session_id=session_id, speaker=speaker, text=text)

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
        speaker=speaker,
        source_text=text,
        translated_text=translated,
    )
    payload = event.model_dump(by_alias=True)
    assert payload["type"] == "translation.final"
    assert payload["sessionId"] == session_id
    assert payload["sourceTs"] == 123
    assert payload["sourceText"] == text
    assert payload["translatedText"] == translated
    assert payload["speaker"] == speaker


def test_event_structure_suggestions() -> None:
    items = [SuggestionItem(en="Question?", ko="질문?")]
    event = SuggestionsUpdateEvent(session_id="sess", items=items)
    payload = event.model_dump(by_alias=True)
    assert payload["type"] == "suggestions.update"
    assert payload["sessionId"] == "sess"
    assert payload["items"][0]["en"] == "Question?"
    assert payload["items"][0]["ko"] == "질문?"


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
    session = MeetingSession("sess")
    text = ". ".join(sentence.strip() for sentence in sentences) + "."
    chunks, remainder = session.add_final_transcript("spk", text)
    assert chunks
    assert remainder == ""
    for chunk in chunks:
        assert chunk[-1] in ".!?"
        assert 1 <= len(re.findall(r"[.!?]", chunk)) <= 2


def test_sentence_boundary_buffering_across_transcripts() -> None:
    session = MeetingSession("sess")
    chunks, remainder = session.add_final_transcript("spk", "This is incomplete")
    assert chunks == []
    assert remainder == "This is incomplete"
    chunks, remainder = session.add_final_transcript("spk", "but now complete.")
    assert chunks == ["This is incomplete but now complete."]
    assert remainder == ""


def test_session_state_accumulation() -> None:
    session = MeetingSession("sess")
    chunks, remainder = session.add_final_transcript("spk", "Hello.")
    assert chunks == ["Hello."]
    assert remainder == ""
    for chunk in chunks:
        session.add_final_chunk("spk", 1, chunk)
    session.add_translation("spk", 1, "Hello.", "안녕하세요.")
    assert len(session.transcripts) == 1
    assert len(session.translations) == 1
