from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class TranslationProvider(ABC):
    @abstractmethod
    def translate_lines(
        self,
        lines: list[str],
        *,
        target_language: str,
        context_hint: Optional[str] = None,
    ) -> list[str]:
        raise NotImplementedError
