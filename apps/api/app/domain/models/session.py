from __future__ import annotations

import re
from dataclasses import dataclass


_SENTENCE_END_RE = re.compile(r"[.!?]")
_SOFT_BOUNDARY_RE = re.compile(
    r"(?:[,;:]$|\b(?:and|but|so|because|if|when|which|that|or|while|then|however|therefore)\b$)",
    re.IGNORECASE,
)
_PARTIAL_UPDATE_INTERVAL_MS = 1500
_PARTIAL_UPDATE_MIN_GROWTH = 18
_PARTIAL_UPDATE_MIN_LENGTH = 32


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
class PartialTranslationState:
    last_complete_sentence: str = ""
    last_partial_source: str = ""
    last_emit_ts: int = 0
    last_emit_length: int = 0


class MeetingSession:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.transcripts: list[TranscriptEntry] = []
        self.translations: list[TranslationEntry] = []
        self._sentence_buffers: dict[str, str] = {}
        self._last_speaker: str | None = None
        self._same_speaker_count = 0
        self._since_last_suggestion = 0
        self._partial_state: dict[str, PartialTranslationState] = {}
        self.suggestions_prompt = ""

    def add_final_transcript(self, speaker: str, text: str) -> tuple[list[str], str]:
        self._partial_state.pop(speaker, None)
        return self._append_text(speaker, text)

    def add_final_chunk(self, speaker: str, ts: int, text: str) -> bool:
        speaker_changed = False
        if self._last_speaker is None:
            self._same_speaker_count = 1
        elif self._last_speaker == speaker:
            self._same_speaker_count += 1
        else:
            speaker_changed = True
            self._same_speaker_count = 1
        self._last_speaker = speaker
        self._since_last_suggestion += 1
        self.transcripts.append(TranscriptEntry(speaker=speaker, ts=ts, text=text))
        return speaker_changed

    def extract_partial_translation(self, speaker: str, ts: int, text: str) -> str | None:
        trimmed = text.strip()
        if not trimmed:
            return None

        state = self._partial_state.get(speaker)
        if state is None:
            state = PartialTranslationState()

        boundary_changed = False
        sentences, _ = self._split_sentences(trimmed)
        if sentences:
            candidate = sentences[-1]
            if candidate != state.last_complete_sentence:
                boundary_changed = True
                state.last_complete_sentence = candidate
                state.last_partial_source = ""
                state.last_emit_ts = 0
                state.last_emit_length = 0
        if len(trimmed) < _PARTIAL_UPDATE_MIN_LENGTH and not boundary_changed:
            self._partial_state[speaker] = state
            return None

        soft_boundary = bool(_SOFT_BOUNDARY_RE.search(trimmed))
        growth = len(trimmed) - state.last_emit_length if state.last_emit_length else len(trimmed)
        time_since = ts - state.last_emit_ts if state.last_emit_ts else None
        time_triggered = (
            state.last_emit_ts > 0
            and time_since is not None
            and time_since >= _PARTIAL_UPDATE_INTERVAL_MS
            and growth >= _PARTIAL_UPDATE_MIN_GROWTH
        )
        first_trigger = state.last_emit_ts == 0 and growth >= _PARTIAL_UPDATE_MIN_GROWTH

        if not (boundary_changed or soft_boundary or time_triggered or first_trigger):
            self._partial_state[speaker] = state
            return None

        if trimmed == state.last_partial_source:
            self._partial_state[speaker] = state
            return None

        state.last_partial_source = trimmed
        state.last_emit_ts = ts
        state.last_emit_length = len(trimmed)
        self._partial_state[speaker] = state
        return trimmed

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
        if len(self.transcripts) < 3:
            return False
        if speaker_changed:
            return True
        return self._same_speaker_count >= 3

    def mark_suggestions_updated(self) -> None:
        self._since_last_suggestion = 0
        self._same_speaker_count = 0
        self._last_speaker = None

    def recent_transcripts(self, limit: int = 10) -> list[TranscriptEntry]:
        return self.transcripts[-limit:]

    def _append_text(self, speaker: str, text: str) -> tuple[list[str], str]:
        buffer = self._sentence_buffers.get(speaker, "")
        combined = f"{buffer} {text}".strip()
        sentences, remainder = self._split_sentences(combined)
        if remainder:
            self._sentence_buffers[speaker] = remainder
        else:
            self._sentence_buffers.pop(speaker, None)
        return self._chunk_sentences(sentences, max_sentences=2), remainder

    @staticmethod
    def _split_sentences(text: str) -> tuple[list[str], str]:
        sentences: list[str] = []
        start = 0
        for match in _SENTENCE_END_RE.finditer(text):
            end = match.end()
            sentence = text[start:end].strip()
            if sentence:
                sentences.append(sentence)
            start = end
        remainder = text[start:].strip()
        return sentences, remainder

    @staticmethod
    def _chunk_sentences(sentences: list[str], max_sentences: int = 2) -> list[str]:
        chunks: list[str] = []
        for index in range(0, len(sentences), max_sentences):
            chunk = " ".join(sentences[index : index + max_sentences]).strip()
            if chunk:
                chunks.append(chunk)
        return chunks
