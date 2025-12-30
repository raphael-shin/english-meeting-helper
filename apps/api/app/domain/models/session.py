from __future__ import annotations

import re
from dataclasses import dataclass

from .subtitle import DisplayBuffer, SubtitleSegment

_SENTENCE_END_RE = re.compile(r"[.!?。？！]")
_CLAUSE_BREAK_RE = re.compile(r"[,;:，、—]")
_SOFT_BOUNDARY_RE = re.compile(
    r"(?:[,;:]$|\b(?:and|but|so|because|if|when|which|that|or|while|then|however|therefore)\b$)",
    re.IGNORECASE,
)
_PARTIAL_UPDATE_INTERVAL_MS = 1000
_PARTIAL_UPDATE_MIN_GROWTH = 10
_PARTIAL_UPDATE_MIN_LENGTH = 18
_MIN_CHARS_FOR_CLAUSE_BREAK = 20
_MAX_SEGMENT_CHARS = 40
_FORCE_SPLIT_CHARS = 60
_CONFIRMED_SUBTITLE_COUNT = 4
_CHUNK_MIN_WORDS = 10
_CHUNK_MAX_WORDS = 25
_CHUNK_MAX_SENTENCES = 2


@dataclass(slots=True)
class TranscriptEntry:
    speaker: str
    ts: int
    text: str


@dataclass(slots=True)
class TranslationEntry:
    speaker: str
    source_ts: int
    source_text: str
    translated_text: str


@dataclass(slots=True)
class FinalChunk:
    speaker: str
    text: str
    segment_id: int
    start_ts: int | None = None


@dataclass(slots=True)
class SentenceBuffer:
    text: str
    start_ts: int
    segment_id: int | None = None


@dataclass(slots=True)
class PartialTranslationState:
    last_complete_sentence: str = ""
    last_caption_text: str = ""
    last_emit_ts: int = 0
    last_emit_length: int = 0
    last_translation_text: str = ""
    last_translation_ts: int = 0
    last_translation_segment_id: int | None = None
    segment_id: int | None = None


@dataclass(slots=True)
class PartialEmit:
    caption_text: str
    translation_text: str | None
    segment_id: int


class MeetingSession:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.transcripts: list[TranscriptEntry] = []
        self.translations: list[TranslationEntry] = []
        self._sentence_buffer: SentenceBuffer | None = None
        self._partial_state: PartialTranslationState | None = None
        self._display_buffer = DisplayBuffer(confirmed=[], current=None)
        self._since_last_suggestion = 0
        self._segment_counter = 0
        self.suggestions_prompt = ""

    def update_display_buffer(self, segment: SubtitleSegment) -> DisplayBuffer:
        if segment.is_final:
            self._display_buffer.confirmed.append(segment)
            if len(self._display_buffer.confirmed) > _CONFIRMED_SUBTITLE_COUNT:
                self._display_buffer.confirmed.pop(0)
            self._display_buffer.current = None
        else:
            self._display_buffer.current = segment
        return self._display_buffer

    def get_display_buffer(self) -> DisplayBuffer:
        return self._display_buffer

    def add_final_transcript(
        self,
        speaker: str,
        text: str,
        ts: int,
    ) -> tuple[str, int]:
        """Add final transcript without chunking.
        
        Returns:
            tuple[str, int]: (text, segment_id)
        """
        partial_state = self._partial_state
        self._partial_state = None
        
        # Use pending segment_id from partial state, or create new one
        if partial_state and partial_state.segment_id is not None:
            segment_id = partial_state.segment_id
        else:
            segment_id = self._next_segment_id()
        
        # Store in transcripts
        speaker = "spk_1"
        self._since_last_suggestion += 1
        self.transcripts.append(TranscriptEntry(speaker=speaker, ts=ts, text=text.strip()))
        
        return text.strip(), segment_id

    def extract_partial_emit(self, speaker: str, ts: int, text: str) -> PartialEmit | None:
        trimmed = text.strip()
        if not trimmed:
            return None

        state = self._partial_state or PartialTranslationState()
        buffer = self._sentence_buffer
        if state.segment_id is None and buffer and buffer.segment_id is not None:
            state.segment_id = buffer.segment_id

        boundary_changed = False
        sentences, remainder = self._split_sentences(trimmed)
        if sentences:
            candidate = sentences[-1]
            if candidate != state.last_complete_sentence:
                boundary_changed = True
                state.last_complete_sentence = candidate
                # Keep state for progressive updates - don't reset

        caption_text = self._build_partial_caption(sentences, remainder)
        if not caption_text:
            self._partial_state = state
            return None
        if len(caption_text) < _PARTIAL_UPDATE_MIN_LENGTH and not boundary_changed:
            self._partial_state = state
            return None

        soft_boundary = bool(_SOFT_BOUNDARY_RE.search(trimmed))
        growth = (
            len(caption_text) - state.last_emit_length
            if state.last_emit_length
            else len(caption_text)
        )
        time_since = ts - state.last_emit_ts if state.last_emit_ts else None
        time_triggered = (
            state.last_emit_ts > 0
            and time_since is not None
            and time_since >= _PARTIAL_UPDATE_INTERVAL_MS
            and growth >= _PARTIAL_UPDATE_MIN_GROWTH
        )
        first_trigger = state.last_emit_ts == 0 and growth >= _PARTIAL_UPDATE_MIN_GROWTH

        if not (boundary_changed or soft_boundary or time_triggered or first_trigger):
            self._partial_state = state
            return None

        if caption_text == state.last_caption_text:
            self._partial_state = state
            return None

        state.last_caption_text = caption_text
        state.last_emit_ts = ts
        state.last_emit_length = len(caption_text)
        if state.segment_id is None:
            state.segment_id = self._next_segment_id()
        translation_text = self._build_translation_chunk(sentences)
        if translation_text and translation_text != state.last_translation_text:
            state.last_translation_text = translation_text
            state.last_translation_ts = ts
            state.last_translation_segment_id = state.segment_id
        else:
            translation_text = None
        self._partial_state = state
        return PartialEmit(
            caption_text=caption_text,
            translation_text=translation_text,
            segment_id=state.segment_id,
        )

    def is_partial_translation_current(
        self,
        speaker: str,
        ts: int,
        text: str,
        segment_id: int,
    ) -> bool:
        state = self._partial_state
        if state is None:
            return False
        return (
            state.last_translation_ts == ts
            and state.last_translation_text == text
            and state.last_translation_segment_id == segment_id
        )

    def add_translation(self, speaker: str, source_ts: int, source_text: str, translated_text: str) -> None:
        self.translations.append(
            TranslationEntry(
                speaker=speaker,
                source_ts=source_ts,
                source_text=source_text,
                translated_text=translated_text,
            )
        )

    def set_suggestions_prompt(self, prompt: str | None) -> None:
        self.suggestions_prompt = (prompt or "").strip()

    def should_update_suggestions(self, speaker_changed: bool) -> bool:
        if len(self.transcripts) < 1:
            return False
        # First suggestion after 1 transcript, then every 2 transcripts
        if self._since_last_suggestion == 0:
            return False
        if len(self.transcripts) == 1:
            return True
        return self._since_last_suggestion >= 2

    def mark_suggestions_updated(self) -> None:
        self._since_last_suggestion = 0

    def recent_transcripts(self, limit: int = 5) -> list[TranscriptEntry]:
        return self.transcripts[-limit:]

    def recent_context(
        self,
        max_sentences: int = 5,
        exclude_ts: int | None = None,
    ) -> list[TranscriptEntry]:
        if max_sentences <= 0:
            return []
        collected: list[TranscriptEntry] = []
        sentence_total = 0
        for entry in reversed(self.transcripts):
            if exclude_ts is not None and entry.ts == exclude_ts:
                continue
            text = entry.text.strip()
            if not text:
                continue
            sentence_count = self._count_sentences(text)
            if sentence_count == 0:
                continue
            collected.append(entry)
            sentence_total += sentence_count
            if sentence_total >= max_sentences:
                break
        return list(reversed(collected))

    def _append_text(
        self,
        text: str,
        ts: int,
        pending_segment_id: int | None,
    ) -> tuple[list[FinalChunk], str]:
        buffer = self._sentence_buffer
        buffer_text = buffer.text if buffer else ""
        combined = f"{buffer_text} {text}".strip()
        sentences, remainder = self._split_sentences(combined)
        if remainder:
            if buffer:
                start_ts = buffer.start_ts
            else:
                start_ts = ts
            if not sentences:
                if buffer and buffer.segment_id is not None:
                    remainder_segment_id = buffer.segment_id
                else:
                    remainder_segment_id = pending_segment_id
            else:
                remainder_segment_id = None
            self._sentence_buffer = SentenceBuffer(
                text=remainder,
                start_ts=start_ts,
                segment_id=remainder_segment_id,
            )
        else:
            self._sentence_buffer = None
        chunks = self._chunk_sentences(sentences)
        final_chunks: list[FinalChunk] = []
        assign_first_segment_id = (
            buffer.segment_id if buffer and buffer.segment_id is not None else None
        )
        assign_last_segment_id = (
            pending_segment_id if assign_first_segment_id is None else None
        )
        last_index = len(chunks) - 1
        for index, chunk in enumerate(chunks):
            start_ts = buffer.start_ts if buffer and index == 0 else None
            if index == 0 and assign_first_segment_id is not None:
                segment_id = assign_first_segment_id
            elif index == last_index and assign_last_segment_id is not None:
                segment_id = assign_last_segment_id
            else:
                segment_id = self._next_segment_id()
            final_chunks.append(
                FinalChunk(
                    speaker="spk_1",
                    text=chunk,
                    segment_id=segment_id,
                    start_ts=start_ts,
                )
            )
        return final_chunks, remainder

    @staticmethod
    def _split_sentences(text: str) -> tuple[list[str], str]:
        return MeetingSession._smart_split_text(text)

    @staticmethod
    def _smart_split_text(text: str) -> tuple[list[str], str]:
        segments: list[str] = []
        current = ""

        for char in text:
            current += char

            if _SENTENCE_END_RE.match(char):
                segment = current.strip()
                if segment:
                    segments.append(segment)
                current = ""
                continue

            if _CLAUSE_BREAK_RE.match(char) and len(current) >= _MIN_CHARS_FOR_CLAUSE_BREAK:
                segment = current.strip()
                if segment:
                    segments.append(segment)
                current = ""
                continue

            if len(current) > _MAX_SEGMENT_CHARS:
                last_space = current.rfind(" ")
                if last_space > 0:
                    segment = current[:last_space].strip()
                    if segment:
                        segments.append(segment)
                    current = current[last_space + 1 :]
                elif len(current) > _FORCE_SPLIT_CHARS:
                    segment = current[:_FORCE_SPLIT_CHARS].strip()
                    if segment:
                        segments.append(segment)
                    current = current[_FORCE_SPLIT_CHARS:].lstrip()

        remainder = current.strip()
        segments = [segment for segment in segments if segment]
        return segments, remainder

    @staticmethod
    def _chunk_sentences(sentences: list[str]) -> list[str]:
        chunks: list[str] = []
        current: list[str] = []
        current_words = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            sentence_words = MeetingSession._count_words(sentence)
            if not current:
                current = [sentence]
                current_words = sentence_words
                continue
            candidate_words = current_words + sentence_words
            if (
                current_words >= _CHUNK_MIN_WORDS
                or len(current) >= _CHUNK_MAX_SENTENCES
                or candidate_words > _CHUNK_MAX_WORDS
            ):
                chunk = " ".join(current).strip()
                if chunk:
                    chunks.append(chunk)
                current = [sentence]
                current_words = sentence_words
                continue
            current.append(sentence)
            current_words = candidate_words
        if current:
            chunk = " ".join(current).strip()
            if chunk:
                chunks.append(chunk)
        return chunks

    def _flush_sentence_buffer(self) -> list[FinalChunk]:
        buffer = self._sentence_buffer
        self._sentence_buffer = None
        if buffer is None:
            return []
        buffer_text = buffer.text.strip()
        if not buffer_text:
            return []
        chunks = self._chunk_text_by_words(buffer_text)
        final_chunks: list[FinalChunk] = []
        for index, chunk in enumerate(chunks):
            segment_id = (
                buffer.segment_id
                if index == 0 and buffer.segment_id is not None
                else self._next_segment_id()
            )
            final_chunks.append(
                FinalChunk(
                    speaker="spk_1",
                    text=chunk,
                    segment_id=segment_id,
                    start_ts=buffer.start_ts,
                )
            )
        return final_chunks

    def _next_segment_id(self) -> int:
        self._segment_counter += 1
        return self._segment_counter

    @staticmethod
    def _chunk_text_by_words(text: str) -> list[str]:
        words = text.split()
        if not words:
            return []
        chunks: list[str] = []
        start = 0
        while start < len(words):
            end = min(start + _CHUNK_MAX_WORDS, len(words))
            chunk = " ".join(words[start:end]).strip()
            if chunk:
                chunks.append(chunk)
            start = end
        return chunks

    @staticmethod
    def _count_words(text: str) -> int:
        return len(text.split())

    @staticmethod
    def _count_sentences(text: str) -> int:
        sentences, remainder = MeetingSession._split_sentences(text)
        count = len(sentences)
        if remainder:
            count += 1
        if count == 0 and text.strip():
            return 1
        return count

    @staticmethod
    def _build_partial_caption(sentences: list[str], remainder: str) -> str:
        # For partial updates, show all accumulated text
        # AWS Transcribe sends complete partial results, not incremental
        parts = sentences + ([remainder] if remainder else [])
        return " ".join(parts).strip()

    @staticmethod
    def _build_translation_chunk(sentences: list[str]) -> str | None:
        if not sentences:
            return None
        return sentences[-1].strip()
