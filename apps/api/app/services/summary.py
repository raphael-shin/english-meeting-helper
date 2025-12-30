from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.domain.models.session import TranscriptEntry
from app.services.translation.aws import AWSTranslationService


class SummaryService:
    def __init__(self, bedrock_service: AWSTranslationService, settings: Settings) -> None:
        self.bedrock = bedrock_service
        self.settings = settings
        self.max_context_chars = 12000

    async def generate_summary(
        self,
        transcripts: list[TranscriptEntry | dict[str, Any]],
    ) -> str | None:
        if not transcripts:
            return None

        context_lines = self._build_context_lines(transcripts)
        if not context_lines:
            return None

        prompt = (
            "You are writing a Meeting Summary for a Korean speaker.\n"
            "Return Markdown only (no code fences, no extra text).\n"
            "Format:\n"
            "## 5줄 요약\n"
            "- Provide exactly 5 short bullet lines.\n"
            "## 핵심 내용\n"
            "- Provide 3 to 7 bullet lines.\n"
            "## Action Items\n"
            "- Provide bullet lines only if action items exist. Otherwise omit this section.\n"
            "Rules:\n"
            "- Keep language simple and natural.\n"
            "- Focus on outcomes and decisions.\n"
            "Transcript:\n"
            f"{chr(10).join(context_lines)}"
        )

        model_id = (
            self.settings.bedrock_translation_high_model_id
            or self.settings.bedrock_translation_fast_model_id
        )
        response = await self.bedrock._invoke_model(model_id, prompt)
        return response.strip() or None

    def _build_context_lines(
        self,
        transcripts: list[TranscriptEntry | dict[str, Any]],
    ) -> list[str]:
        lines = []
        for entry in transcripts:
            if isinstance(entry, TranscriptEntry):
                speaker = entry.speaker
                text = entry.text
            else:
                speaker = str(entry.get("speaker", "spk"))
                text = str(entry.get("text", ""))
            text = text.strip()
            if not text:
                continue
            lines.append(f"{speaker}: {text}")

        if not lines:
            return []

        total_chars = sum(len(line) for line in lines)
        if total_chars <= self.max_context_chars:
            return lines

        trimmed: list[str] = []
        current = 0
        for line in reversed(lines):
            line_len = len(line)
            if current + line_len > self.max_context_chars:
                break
            trimmed.append(line)
            current += line_len
        return list(reversed(trimmed))
