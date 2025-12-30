from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

__all__ = ["SubtitleSegment", "DisplayBuffer"]


@dataclass(slots=True)
class SubtitleSegment:
    id: str
    text: str
    speaker: str
    start_time: int
    end_time: Optional[int]
    is_final: bool
    llm_corrected: bool
    segment_id: int
    translation: Optional[str] = None


@dataclass(slots=True)
class DisplayBuffer:
    confirmed: list[SubtitleSegment]
    current: Optional[SubtitleSegment]
