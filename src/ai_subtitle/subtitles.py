from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union


@dataclass
class SubtitleEntry:
    index: int
    start: str
    end: str
    text: str


def parse_srt(path: Union[str, Path]) -> list[SubtitleEntry]:
    content = Path(path).read_text(encoding="utf-8-sig")
    blocks = [block.strip() for block in content.split("\n\n") if block.strip()]
    entries: list[SubtitleEntry] = []

    for block in blocks:
        lines = [line.rstrip("\r") for line in block.splitlines()]
        if len(lines) < 3:
            continue

        index = int(lines[0].strip())
        timing = lines[1].strip()
        if " --> " not in timing:
            continue

        start, end = timing.split(" --> ", maxsplit=1)
        text = "\n".join(lines[2:]).strip()

        entries.append(
            SubtitleEntry(
                index=index,
                start=start,
                end=end,
                text=text,
            )
        )

    return entries


def write_srt(path: Union[str, Path], entries: list[SubtitleEntry]) -> None:
    output_blocks: list[str] = []
    for entry in entries:
        block = "\n".join(
            [
                str(entry.index),
                f"{entry.start} --> {entry.end}",
                entry.text.strip(),
            ]
        )
        output_blocks.append(block)

    Path(path).write_text(
        "\n\n".join(output_blocks).strip() + "\n",
        encoding="utf-8",
    )
