from app.domain.models.session import MeetingSession, _FORCE_SPLIT_CHARS


def test_smart_split_sentence_enders() -> None:
    text = "Hello world. How are you?"
    segments, remainder = MeetingSession._smart_split_text(text)
    assert segments == ["Hello world.", "How are you?"]
    assert remainder == ""


def test_smart_split_clause_break() -> None:
    text = "First item is important, second is optional"
    segments, remainder = MeetingSession._smart_split_text(text)
    assert any("important," in segment for segment in segments)
    assert remainder == "second is optional"


def test_smart_split_length_based() -> None:
    text = "This is a very long sentence without any punctuation marks"
    segments, remainder = MeetingSession._smart_split_text(text)
    assert segments
    assert remainder


def test_smart_split_force() -> None:
    text = "A" * (_FORCE_SPLIT_CHARS + 5)
    segments, remainder = MeetingSession._smart_split_text(text)
    assert segments
    assert len(segments[0]) <= _FORCE_SPLIT_CHARS
    assert remainder == "A" * 5
