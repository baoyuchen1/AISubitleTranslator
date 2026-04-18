from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional

from mss import mss
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

from ai_subtitle.overlay import OverlayWindow
from ai_subtitle.providers.base import TranslationProvider


@dataclass
class ScreenRegion:
    left: int
    top: int
    width: int
    height: int


class GameOCRTranslator:
    def __init__(
        self,
        *,
        provider: TranslationProvider,
        target_language: str,
        region: ScreenRegion,
        interval_seconds: float = 0.8,
        similarity_threshold: float = 0.92,
        min_display_seconds: float = 2.2,
        max_display_seconds: float = 5.5,
    ) -> None:
        self._provider = provider
        self._target_language = target_language
        self._region = region
        self._interval_seconds = interval_seconds
        self._similarity_threshold = similarity_threshold
        self._min_display_seconds = min_display_seconds
        self._max_display_seconds = max_display_seconds
        self._ocr = RapidOCR()
        self._last_source_text = ""
        self._active_overlay_text = ""
        self._display_deadline: Optional[float] = None
        self._stop_event = threading.Event()
        self._worker: Optional[threading.Thread] = None

    def run(self) -> None:
        overlay = OverlayWindow()
        self.start(overlay)
        try:
            overlay.run()
        finally:
            self.stop()

    def start(self, overlay: OverlayWindow) -> None:
        if self.is_running:
            raise RuntimeError("Game OCR translator is already running.")

        self._stop_event.clear()
        self._worker = threading.Thread(
            target=self._capture_loop,
            args=(overlay,),
            daemon=True,
        )
        self._worker.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._worker is not None and self._worker.is_alive():
            self._worker.join(timeout=1.5)
        self._worker = None

    @property
    def is_running(self) -> bool:
        return self._worker is not None and self._worker.is_alive()

    def _capture_loop(self, overlay: OverlayWindow) -> None:
        with mss() as sct:
            while not self._stop_event.is_set():
                self._maybe_clear_overlay(overlay)
                try:
                    screenshot = sct.grab(
                        {
                            "left": self._region.left,
                            "top": self._region.top,
                            "width": self._region.width,
                            "height": self._region.height,
                        }
                    )
                    image = Image.frombytes(
                        "RGB",
                        screenshot.size,
                        screenshot.rgb,
                    )

                    source_text = self._extract_text(image)
                    if not source_text:
                        if self._wait_for_next_tick():
                            break
                        continue

                    if self._is_similar_to_last(source_text):
                        if self._wait_for_next_tick():
                            break
                        continue

                    self._last_source_text = source_text
                    translated = self._provider.translate_lines(
                        [source_text],
                        target_language=self._target_language,
                        context_hint="Game subtitle translation. Keep it short enough for real-time reading.",
                    )[0]
                    overlay.set_text(translated)
                    self._active_overlay_text = translated
                    self._display_deadline = (
                        time.monotonic() + self._compute_display_seconds(translated)
                    )
                except Exception as exc:
                    error_text = f"OCR error: {exc}"
                    overlay.set_text(error_text)
                    self._active_overlay_text = error_text
                    self._display_deadline = time.monotonic() + self._min_display_seconds

                if self._wait_for_next_tick():
                    break

    def _extract_text(self, image: Image.Image) -> str:
        result, _ = self._ocr(image)
        if not result:
            return ""

        lines: list[str] = []
        for item in result:
            if len(item) < 2:
                continue
            text = str(item[1]).strip()
            if text:
                lines.append(text)

        return "\n".join(lines).strip()

    def _is_similar_to_last(self, current_text: str) -> bool:
        if not self._last_source_text:
            return False

        similarity = SequenceMatcher(
            a=self._last_source_text,
            b=current_text,
        ).ratio()
        return similarity >= self._similarity_threshold

    def _wait_for_next_tick(self) -> bool:
        return self._stop_event.wait(self._interval_seconds)

    def _maybe_clear_overlay(self, overlay: OverlayWindow) -> None:
        if not self._active_overlay_text or self._display_deadline is None:
            return

        if time.monotonic() < self._display_deadline:
            return

        overlay.clear_text()
        self._active_overlay_text = ""
        self._display_deadline = None

    def _compute_display_seconds(self, text: str) -> float:
        readable_text = "".join(text.split())
        if not readable_text:
            return self._min_display_seconds

        estimated = 1.4 + (len(readable_text) / 7.5)
        return max(
            self._min_display_seconds,
            min(self._max_display_seconds, estimated),
        )
