from __future__ import annotations

import json
from typing import Dict, Optional

import httpx

from ai_subtitle.config import AppConfig
from ai_subtitle.providers.base import TranslationProvider


SYSTEM_PROMPT = """You are a professional game and subtitle translator.
Translate every input line into the target language.
Rules:
1. Keep the number of output items exactly the same as input items.
2. Return JSON only.
3. Use this JSON shape: {"translations": ["...", "..."]}.
4. Preserve speaker tone, names, and formatting markers when possible.
5. Do not add explanations."""


class OpenAICompatibleProvider(TranslationProvider):
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def translate_lines(
        self,
        lines: list[str],
        *,
        target_language: str,
        context_hint: Optional[str] = None,
    ) -> list[str]:
        if not lines:
            return []

        user_payload = {
            "target_language": target_language,
            "context_hint": context_hint or "",
            "lines": lines,
        }

        response = httpx.post(
            f"{self._config.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._config.model,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": json.dumps(
                            user_payload,
                            ensure_ascii=False,
                        ),
                    },
                ],
            },
            timeout=self._config.timeout,
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = _parse_json_object(content)
        translations = parsed["translations"]

        if not isinstance(translations, list):
            raise ValueError("Model output is missing a translations list.")
        if len(translations) != len(lines):
            raise ValueError(
                "Model returned a different number of translations than input lines."
            )

        return [str(item).strip() for item in translations]


def _parse_json_object(content: str) -> Dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model response does not contain a JSON object.") from None

        return json.loads(content[start : end + 1])
