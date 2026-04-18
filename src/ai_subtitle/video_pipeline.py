from __future__ import annotations

from itertools import islice
from typing import Iterator, TypeVar

from ai_subtitle.providers.base import TranslationProvider
from ai_subtitle.subtitles import SubtitleEntry, parse_srt, write_srt


T = TypeVar("T")


def chunked(items: list[T], size: int) -> Iterator[list[T]]:
    iterator = iter(items)
    while chunk := list(islice(iterator, size)):
        yield chunk


def translate_srt(
    input_path: str,
    output_path: str,
    *,
    provider: TranslationProvider,
    target_language: str,
    bilingual: bool = False,
    batch_size: int = 20,
) -> None:
    entries = parse_srt(input_path)
    translated_entries: list[SubtitleEntry] = []

    for batch in chunked(entries, batch_size):
        source_lines = [entry.text for entry in batch]
        translated_lines = provider.translate_lines(
            source_lines,
            target_language=target_language,
            context_hint="Video subtitle translation. Keep wording natural and concise.",
        )

        if len(batch) != len(translated_lines):
            raise ValueError("Batch translation count does not match input count.")

        for entry, translated in zip(batch, translated_lines):
            new_text = translated
            if bilingual:
                new_text = f"{entry.text}\n{translated}"

            translated_entries.append(
                SubtitleEntry(
                    index=entry.index,
                    start=entry.start,
                    end=entry.end,
                    text=new_text,
                )
            )

    write_srt(output_path, translated_entries)
