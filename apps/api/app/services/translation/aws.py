from __future__ import annotations

import asyncio
import json
from typing import Any

import boto3

from app.core.config import Settings


class AWSTranslationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = boto3.client("bedrock-runtime", region_name=settings.aws_region)

    async def translate_en_to_ko(self, text: str) -> str:
        prompt = (
            "Translate the following English text to natural Korean.\n"
            f"\"{text}\"\n"
            "Return only the Korean translation. Do not ask questions or add explanations."
        )
        response = await self._invoke_model(self.settings.bedrock_translation_model_id, prompt)
        return response.strip()

    async def translate_en_to_ko_history(
        self,
        text: str,
        recent_context: list[str] | None = None,
    ) -> str:
        model_id = self.settings.bedrock_translation_high_model_id or self.settings.bedrock_translation_model_id
        prompt = self._build_history_prompt(text, recent_context)
        response = await self._invoke_model(model_id, prompt)
        return response.strip()

    async def translate_for_display(
        self,
        text: str,
        confirmed_texts: list[str],
    ) -> str:
        """Translate for Live display with confirmed context."""
        prompt_lines = [
            "You are a real-time meeting translator. Translate English to natural Korean.",
            "Use the confirmed context below for coherence and consistency.",
            "Translate only the current sentence, maintaining flow with previous translations.",
            "Identify key terms (technical terms, proper nouns, important concepts) and wrap them with **word**.",
            "Never ask questions or add explanations. Respond in Korean only.",
        ]
        if confirmed_texts:
            prompt_lines.append("\nConfirmed context (most recent first):")
            prompt_lines.extend(f"- {ctx}" for ctx in confirmed_texts[:4])
        prompt_lines.append(f"\nCurrent sentence: \"{text}\"")
        prompt_lines.append("Return only the Korean translation.")
        
        prompt = "\n".join(prompt_lines)
        model_id = self.settings.bedrock_translation_high_model_id or self.settings.bedrock_translation_model_id
        response = await self._invoke_model(model_id, prompt)
        return response.strip()

    async def translate_ko_to_en(self, text: str) -> str:
        prompt = (
            "Translate the following Korean text to natural English:\n"
            f"\"{text}\"\n"
            "Return only the translation, no explanation."
        )
        response = await self._invoke_model(self.settings.bedrock_quick_translate_model_id, prompt)
        return response.strip()

    async def invoke_correction(self, prompt: str) -> str:
        response = await self._invoke_model(self.settings.bedrock_correction_model_id, prompt)
        return response.strip()

    async def _invoke_model(self, model_id: str, prompt: str) -> str:
        response = await asyncio.to_thread(
            self.client.converse,
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            inferenceConfig={
                "maxTokens": 512,
                "temperature": 0.2,
            },
        )
        return self._extract_text(response)

    @staticmethod
    def _build_history_prompt(text: str, recent_context: list[str] | None) -> str:
        lines = [
            "You are a translator. Translate English to natural Korean.",
            "Use context for coherence but translate only the current line.",
            "If the line is unclear or incomplete, make the best possible inference.",
            "Never ask questions, request more context, or mention language selection.",
            "Respond in Korean only, without quotes or extra text.",
        ]
        if recent_context:
            lines.append("Recent context:")
            lines.extend(f"- {entry}" for entry in recent_context)
        lines.append(f"Current line: \"{text}\"")
        lines.append("Return only the translation.")
        return "\n".join(lines)

    @staticmethod
    def _extract_text(response: dict[str, Any]) -> str:
        if "output" in response:
            return AWSTranslationService._extract_converse_text(response)
        body = response.get("body")
        if body is None:
            return ""
        if hasattr(body, "read"):
            raw = body.read()
        else:
            raw = body
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return raw.strip()
        else:
            data = raw

        if isinstance(data, dict):
            if "outputText" in data:
                return str(data["outputText"])
            if "completion" in data:
                return str(data["completion"])
            if "results" in data and data["results"]:
                return str(data["results"][0].get("outputText", ""))
            if "content" in data and data["content"]:
                return str(data["content"][0].get("text", ""))
        return ""

    @staticmethod
    def _extract_converse_text(response: dict[str, Any]) -> str:
        output = response.get("output") or {}
        message = output.get("message") or {}
        content = message.get("content") or []
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    texts.append(str(item["text"]))
                elif isinstance(item, str):
                    texts.append(item)
            return "".join(texts).strip()
        return str(content).strip()
