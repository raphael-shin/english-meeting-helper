from __future__ import annotations

import json
import re
from typing import Any

from app.core.config import Settings
from app.domain.models.session import TranscriptEntry
from app.services.translation.aws import AWSTranslationService


class SuggestionService:
    def __init__(self, bedrock_service: AWSTranslationService, settings: Settings) -> None:
        self.bedrock = bedrock_service
        self.settings = settings
        self.min_transcripts_for_suggestion = 3

    async def generate_suggestions(
        self,
        transcripts: list[TranscriptEntry | dict[str, Any]],
        system_prompt: str | None = None,
    ) -> list[dict[str, str]]:
        if len(transcripts) < self.min_transcripts_for_suggestion:
            return []

        context_lines = []
        for entry in transcripts[-10:]:
            if isinstance(entry, TranscriptEntry):
                speaker = entry.speaker
                text = entry.text
            else:
                speaker = str(entry.get("speaker", "spk"))
                text = str(entry.get("text", ""))
            context_lines.append(f"- {speaker}: {text}")

        system_prompt = (system_prompt or "").strip()
        prompt_prefix = ""
        if system_prompt:
            prompt_prefix = (
                "Use the following system prompt to guide the suggestions.\n"
                f"System prompt:\n{system_prompt}\n\n"
            )

        prompt = (
            f"{prompt_prefix}"
            "You are helping a non-native speaker participate in a meeting. "
            "Suggest 5 short, natural English sentences they can say. Mix questions and answers.\n"
            "Rules:\n"
            "- Use simple, easy-to-edit phrases.\n"
            "- Keep each sentence under 12 words.\n"
            "- Avoid jargon and idioms.\n"
            "- Make them sound polite and natural.\n"
            "Return a JSON array of objects with keys \"en\" and \"ko\" only.\n"
            "Context:\n"
            f"{chr(10).join(context_lines)}"
        )

        response = await self.bedrock._invoke_model(self.settings.bedrock_translation_fast_model_id, prompt)
        return self._parse_suggestions(response)

    @staticmethod
    def _parse_suggestions(response: str) -> list[dict[str, str]]:
        response = response.strip()
        if not response:
            return []

        data = SuggestionService._try_parse_json(response)
        if isinstance(data, list):
            items = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                en = str(item.get("en", "")).strip()
                ko = str(item.get("ko", "")).strip()
                if en and ko:
                    items.append({"en": en, "ko": ko})
            return items[:5]

        suggestions: list[dict[str, str]] = []
        for line in response.splitlines():
            line = line.strip().lstrip("-").strip()
            if not line:
                continue
            if "|" in line:
                en, ko = [part.strip() for part in line.split("|", 1)]
            elif "-" in line:
                en, ko = [part.strip() for part in line.split("-", 1)]
            else:
                continue
            if en and ko:
                suggestions.append({"en": en, "ko": ko})
        return suggestions[:5]

    @staticmethod
    def _try_parse_json(response: str) -> Any:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", response, re.DOTALL)
            if not match:
                return None
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
