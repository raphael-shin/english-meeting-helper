from __future__ import annotations

import asyncio
import json
import logging
from typing import Iterable

from app.domain.models.subtitle import SubtitleSegment
from app.services.translation.aws import AWSTranslationService

logger = logging.getLogger(__name__)


class CorrectionQueue:
    def __init__(
        self,
        bedrock_service: AWSTranslationService,
        batch_size: int,
    ) -> None:
        self._queue: asyncio.Queue[SubtitleSegment] = asyncio.Queue()
        self._bedrock = bedrock_service
        self._batch_size = batch_size

    async def enqueue(self, segment: SubtitleSegment) -> None:
        await self._queue.put(segment)

    async def process_batch(self) -> list[tuple[int, str, str]]:
        batch = self._drain_batch()
        if not batch:
            return []
        try:
            return await self._correct_batch(batch)
        except Exception:
            logger.exception("LLM correction batch failed")
            return []

    def _drain_batch(self) -> list[SubtitleSegment]:
        batch: list[SubtitleSegment] = []
        for _ in range(self._batch_size):
            if self._queue.empty():
                break
            try:
                batch.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return batch

    async def _correct_batch(
        self, segments: list[SubtitleSegment]
    ) -> list[tuple[int, str, str]]:
        prompt = self._build_correction_prompt(segments)
        response_text = await self._bedrock.invoke_correction(prompt)
        return self._parse_corrections(response_text, segments)

    @staticmethod
    def _build_correction_prompt(segments: Iterable[SubtitleSegment]) -> str:
        lines = [f"{index + 1}. {segment.text}" for index, segment in enumerate(segments)]
        return (
            "Fix typos and spacing in the following live transcript lines.\n"
            "Rules:\n"
            "- Preserve meaning.\n"
            "- Keep proper nouns consistent (e.g., AWS, API).\n"
            "- Make minimal edits.\n"
            "Input:\n"
            + "\n".join(lines)
            + "\n\nRespond in JSON:\n"
            + '{"corrections": ["corrected 1", "corrected 2", "..."]}'
        )

    @staticmethod
    def _parse_corrections(
        response_text: str, segments: list[SubtitleSegment]
    ) -> list[tuple[int, str, str]]:
        data = CorrectionQueue._load_json(response_text)
        if not isinstance(data, dict):
            return []
        corrections_list = data.get("corrections")
        if not isinstance(corrections_list, list):
            return []
        result: list[tuple[int, str, str]] = []
        for index, corrected in enumerate(corrections_list):
            if index >= len(segments):
                break
            if not isinstance(corrected, str):
                continue
            segment = segments[index]
            corrected_text = corrected.strip()
            if corrected_text and corrected_text != segment.text:
                result.append((segment.segment_id, segment.text, corrected_text))
        return result

    @staticmethod
    def _load_json(text: str) -> dict | list | None:
        trimmed = text.strip()
        if not trimmed:
            return None
        try:
            return json.loads(trimmed)
        except json.JSONDecodeError:
            start = trimmed.find("{")
            end = trimmed.rfind("}")
            if start == -1 or end == -1 or start >= end:
                return None
            try:
                return json.loads(trimmed[start : end + 1])
            except json.JSONDecodeError:
                return None
