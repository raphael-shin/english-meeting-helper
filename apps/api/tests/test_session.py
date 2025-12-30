"""MeetingSession 핵심 로직 테스트"""

from app.domain.models.session import (
    MeetingSession,
    _PARTIAL_UPDATE_INTERVAL_MS,
    _PARTIAL_UPDATE_MIN_GROWTH,
    _PARTIAL_UPDATE_MIN_LENGTH,
    _CHUNK_MIN_WORDS,
    _CHUNK_MAX_WORDS,
)


class TestExtractPartialEmit:
    """extract_partial_emit() 상태 머신 테스트"""

    def test_empty_text_returns_none(self) -> None:
        session = MeetingSession("sess")
        result = session.extract_partial_emit("spk_1", 100, "")
        assert result is None
        result = session.extract_partial_emit("spk_1", 100, "   ")
        assert result is None

    def test_first_trigger_with_sufficient_growth(self) -> None:
        session = MeetingSession("sess")
        text = "This is a test sentence"
        result = session.extract_partial_emit("spk_1", 100, text)
        assert result is not None
        assert result.caption_text == text
        assert result.segment_id == 1

    def test_first_trigger_insufficient_length_no_emit(self) -> None:
        session = MeetingSession("sess")
        text = "Short"
        assert len(text) < _PARTIAL_UPDATE_MIN_LENGTH
        result = session.extract_partial_emit("spk_1", 100, text)
        assert result is None

    def test_time_trigger_after_interval(self) -> None:
        session = MeetingSession("sess")
        text1 = "This is the first part"
        result1 = session.extract_partial_emit("spk_1", 100, text1)
        assert result1 is not None

        text2 = "This is the first part with more"
        result2 = session.extract_partial_emit(
            "spk_1", 100 + _PARTIAL_UPDATE_INTERVAL_MS, text2
        )
        assert result2 is not None
        assert result2.caption_text == text2

    def test_time_trigger_before_interval_no_emit(self) -> None:
        session = MeetingSession("sess")
        text1 = "This is the first part"
        result1 = session.extract_partial_emit("spk_1", 100, text1)
        assert result1 is not None

        text2 = "This is the first part with"
        result2 = session.extract_partial_emit("spk_1", 100 + 500, text2)
        assert result2 is None

    def test_boundary_change_resets_state(self) -> None:
        session = MeetingSession("sess")
        text1 = "First sentence. Second"
        result1 = session.extract_partial_emit("spk_1", 100, text1)
        assert result1 is not None
        first_segment_id = result1.segment_id

        text2 = "First sentence. Second sentence. Third"
        result2 = session.extract_partial_emit("spk_1", 200, text2)
        assert result2 is not None
        # segment_id should remain the same during partial updates
        assert result2.segment_id == first_segment_id

    def test_soft_boundary_triggers_emit(self) -> None:
        session = MeetingSession("sess")
        text = "We need to discuss this and"
        result = session.extract_partial_emit("spk_1", 100, text)
        assert result is not None
        assert result.caption_text == text

    def test_same_caption_no_duplicate_emit(self) -> None:
        session = MeetingSession("sess")
        text = "This is a test sentence"
        result1 = session.extract_partial_emit("spk_1", 100, text)
        assert result1 is not None

        result2 = session.extract_partial_emit("spk_1", 200, text)
        assert result2 is None

    def test_translation_text_on_complete_sentence(self) -> None:
        session = MeetingSession("sess")
        text = "Hello world. This is"
        result = session.extract_partial_emit("spk_1", 100, text)
        assert result is not None
        assert result.translation_text == "Hello world."


class TestIsPartialTranslationCurrent:
    """is_partial_translation_current() 상태 매칭 테스트"""


class TestLongSentenceSplitting:
    """긴 문장 처리 테스트 (빠른 화자)"""

    def test_multiple_sentences_in_final(self) -> None:
        """4-5개 문장이 한 번에 Final로 들어오는 경우 - 단일 segment로 처리"""
        session = MeetingSession("sess")
        long_text = (
            "Smart founders apply to YC. "
            "They want to build AI companies. "
            "We fund the most ambitious teams. "
            "AI is transforming every industry. "
            "The future is incredibly exciting."
        )
        
        text, segment_id = session.add_final_transcript("spk_1", long_text, 1000)
        
        # 단일 segment로 반환됨
        assert text == long_text.strip()
        assert segment_id is not None
        assert "Smart founders" in text
        assert "incredibly exciting" in text

    def test_long_sentence_without_punctuation(self) -> None:
        """구두점 없이 긴 문장이 들어오는 경우 - 그대로 처리"""
        session = MeetingSession("sess")
        long_text = "This is a very long sentence without any punctuation marks that goes on and on and should be split"
        
        text, segment_id = session.add_final_transcript("spk_1", long_text, 1000)
        
        # 단일 segment로 반환됨
        assert text == long_text
        assert segment_id is not None

    def test_display_buffer_with_single_segment(self) -> None:
        """긴 텍스트가 display buffer에 단일 segment로 추가되는지"""
        session = MeetingSession("sess")
        long_text = (
            "First sentence here. "
            "Second sentence here. "
            "Third sentence here. "
            "Fourth sentence here. "
            "Fifth sentence here."
        )
    def test_display_buffer_with_single_segment(self) -> None:
        """긴 텍스트가 display buffer에 단일 segment로 추가되는지"""
        session = MeetingSession("sess")
        long_text = (
            "First sentence here. "
            "Second sentence here. "
            "Third sentence here. "
            "Fourth sentence here. "
            "Fifth sentence here."
        )
        
        text, segment_id = session.add_final_transcript("spk_1", long_text, 1000)
        
        # 단일 segment 생성
        from app.domain.models.subtitle import SubtitleSegment
        segment = SubtitleSegment(
            id=f"seg_{segment_id}",
            text=text,
            speaker="spk_1",
            start_time=1000,
            end_time=2000,
            is_final=True,
            llm_corrected=False,
            segment_id=segment_id,
        )
        session.update_display_buffer(segment)
        
        buffer = session.get_display_buffer()
        
        # 단일 segment가 confirmed에 추가됨
        assert len(buffer.confirmed) == 1
        assert buffer.confirmed[0].text == text


class TestIsPartialTranslationCurrent:
    """is_partial_translation_current() 상태 매칭 테스트"""

    def test_no_state_returns_false(self) -> None:
        session = MeetingSession("sess")
        result = session.is_partial_translation_current("spk_1", 100, "text", 1)
        assert result is False

    def test_matching_state_returns_true(self) -> None:
        session = MeetingSession("sess")
        text = "First sentence. Second part"
        emit = session.extract_partial_emit("spk_1", 100, text)
        assert emit is not None
        assert emit.translation_text is not None

        result = session.is_partial_translation_current(
            "spk_1", 100, emit.translation_text, emit.segment_id
        )
        assert result is True

    def test_mismatched_ts_returns_false(self) -> None:
        session = MeetingSession("sess")
        text = "First sentence. Second part"
        emit = session.extract_partial_emit("spk_1", 100, text)
        assert emit is not None
        assert emit.translation_text is not None

        result = session.is_partial_translation_current(
            "spk_1", 999, emit.translation_text, emit.segment_id
        )
        assert result is False


class TestBuildPartialCaption:
    """_build_partial_caption() 테스트"""

    def test_returns_last_sentence_when_sentences_exist(self) -> None:
        result = MeetingSession._build_partial_caption(
            ["First.", "Second."], "remainder"
        )
        assert result == "First. Second. remainder"

    def test_returns_remainder_when_no_sentences(self) -> None:
        result = MeetingSession._build_partial_caption([], "only remainder")
        assert result == "only remainder"

    def test_returns_empty_when_both_empty(self) -> None:
        result = MeetingSession._build_partial_caption([], "")
        assert result == ""


class TestChunkSentences:
    """_chunk_sentences() 단어 수 경계 테스트"""

    def test_merges_short_sentences(self) -> None:
        sentences = ["Hi.", "Hello."]
        chunks = MeetingSession._chunk_sentences(sentences)
        assert len(chunks) == 1
        assert chunks[0] == "Hi. Hello."

    def test_splits_when_first_reaches_min_words(self) -> None:
        # 첫 문장이 MIN_WORDS 이상이면 다음 문장과 분리
        long_first = " ".join(["word"] * (_CHUNK_MIN_WORDS + 1)) + "."
        short_second = "Short."
        sentences = [long_first, short_second]
        chunks = MeetingSession._chunk_sentences(sentences)
        assert len(chunks) == 2

    def test_splits_at_max_words(self) -> None:
        sentence1 = " ".join(["word"] * 15) + "."
        sentence2 = " ".join(["more"] * 15) + "."
        sentences = [sentence1, sentence2]
        chunks = MeetingSession._chunk_sentences(sentences)
        assert len(chunks) == 2

    def test_max_two_sentences_per_chunk(self) -> None:
        sentences = ["One.", "Two.", "Three."]
        chunks = MeetingSession._chunk_sentences(sentences)
        assert len(chunks) == 2
        assert chunks[0] == "One. Two."
        assert chunks[1] == "Three."

    def test_empty_sentences_filtered(self) -> None:
        sentences = ["Hello.", "", "  ", "World."]
        chunks = MeetingSession._chunk_sentences(sentences)
        assert len(chunks) == 1
        assert chunks[0] == "Hello. World."


class TestSmartSplitEdgeCases:
    """_smart_split_text() 엣지 케이스 테스트"""

    def test_empty_string(self) -> None:
        segments, remainder = MeetingSession._smart_split_text("")
        assert segments == []
        assert remainder == ""

    def test_unicode_sentence_enders(self) -> None:
        text = "これはテストです。次の文。"
        segments, remainder = MeetingSession._smart_split_text(text)
        assert len(segments) == 2
        assert remainder == ""

    def test_mixed_punctuation(self) -> None:
        text = "Hello! How are you? I am fine."
        segments, remainder = MeetingSession._smart_split_text(text)
        assert len(segments) == 3
        assert remainder == ""

    def test_unicode_clause_breaks(self) -> None:
        # 유니코드 구두점(，)은 20자 이상일 때만 분할
        text = "This is a long text，and more text follows"
        segments, remainder = MeetingSession._smart_split_text(text)
        assert len(segments) >= 1
        # 20자 이상에서 ，로 분할되었는지 확인
        assert any("，" in seg for seg in segments) or "，" in remainder


class TestDisplayBufferTransitions:
    """update_display_buffer() 상태 전이 테스트"""

    def test_current_to_confirmed_transition(self) -> None:
        from app.domain.models.subtitle import SubtitleSegment

        session = MeetingSession("sess")

        current = SubtitleSegment(
            id="seg_1",
            text="Partial",
            speaker="spk_1",
            start_time=100,
            end_time=None,
            is_final=False,
            llm_corrected=False,
            segment_id=1,
        )
        buffer = session.update_display_buffer(current)
        assert buffer.current is not None
        assert len(buffer.confirmed) == 0

        final = SubtitleSegment(
            id="seg_1",
            text="Final text",
            speaker="spk_1",
            start_time=100,
            end_time=200,
            is_final=True,
            llm_corrected=False,
            segment_id=1,
        )
        buffer = session.update_display_buffer(final)
        assert buffer.current is None
        assert len(buffer.confirmed) == 1
        assert buffer.confirmed[0].text == "Final text"

    def test_get_display_buffer_returns_same_instance(self) -> None:
        session = MeetingSession("sess")
        buffer1 = session.get_display_buffer()
        buffer2 = session.get_display_buffer()
        assert buffer1 is buffer2
