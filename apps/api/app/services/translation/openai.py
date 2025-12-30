from __future__ import annotations

from openai import AsyncOpenAI

from app.core.config import Settings


class OpenAITranslationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def translate_en_to_ko(self, text: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.settings.openai_translation_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a translator. Translate English to natural Korean. "
                        "Return only the translation in Korean. "
                        "Do not ask questions or add explanations."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()

    async def translate_en_to_ko_history(
        self,
        text: str,
        recent_context: list[str] | None = None,
    ) -> str:
        system_prompt = (
            "You are a translator. Translate English to natural Korean. "
            "Use context for coherence but translate only the current line. "
            "If the line is unclear or incomplete, make the best possible inference. "
            "Never ask questions, request more context, or mention language selection. "
            "Respond in Korean only, without quotes or extra text. Return only the translation."
        )
        user_lines: list[str] = []
        if recent_context:
            user_lines.append("Recent context:")
            user_lines.extend(f"- {entry}" for entry in recent_context)
        user_lines.append(f"Current line: \"{text}\"")
        response = await self.client.chat.completions.create(
            model=self.settings.openai_translation_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "\n".join(user_lines)},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()

    async def translate_ko_to_en(self, text: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.settings.openai_translation_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a translator. Translate Korean to natural English. Return only the translation.",
                },
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()
