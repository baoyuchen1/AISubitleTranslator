from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Union

from ai_subtitle.subtitles import SubtitleEntry, write_srt


@dataclass
class TranscriptionResult:
    detected_language: str
    segment_count: int
    duration_seconds: Optional[float]


def transcribe_media_to_srt(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    model_size: str = "small",
    language: Optional[str] = None,
    device: str = "auto",
    compute_type: str = "int8",
    beam_size: int = 5,
    vad_filter: bool = True,
    status_callback: Optional[Callable[[str], None]] = None,
) -> TranscriptionResult:
    def emit_status(message: str) -> None:
        if status_callback is not None:
            status_callback(message)

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: faster-whisper. Rebuild or reinstall the app dependencies."
        ) from exc

    source_path = Path(input_path)
    target_path = Path(output_path)

    if not source_path.exists():
        raise FileNotFoundError(f"Input media file not found: {source_path}")

    active_device = device
    active_compute_type = compute_type

    try:
        emit_status(
            f"Loading Whisper model on {active_device}. First run may take a while if the model needs to be downloaded."
        )
        model = WhisperModel(model_size, device=active_device, compute_type=active_compute_type)
        emit_status("Whisper model ready. Starting transcription...")
        segments, info = model.transcribe(
            str(source_path),
            language=None if not language or language.lower() == "auto" else language,
            task="transcribe",
            beam_size=beam_size,
            vad_filter=vad_filter,
            condition_on_previous_text=True,
        )
    except RuntimeError as exc:
        if not _should_fallback_to_cpu(active_device, exc):
            raise

        emit_status(
            "CUDA runtime is unavailable on this machine. Falling back to CPU transcription."
        )
        active_device = "cpu"
        active_compute_type = "int8"
        model = WhisperModel(model_size, device=active_device, compute_type=active_compute_type)
        emit_status("CPU Whisper model ready. Restarting transcription...")
        segments, info = model.transcribe(
            str(source_path),
            language=None if not language or language.lower() == "auto" else language,
            task="transcribe",
            beam_size=beam_size,
            vad_filter=vad_filter,
            condition_on_previous_text=True,
        )

    entries: list[SubtitleEntry] = []
    emit_status("Transcription in progress. Waiting for segments...")
    for segment in segments:
        text = (segment.text or "").strip()
        if not text:
            continue

        start = float(segment.start or 0.0)
        end = float(segment.end or start)
        if end <= start:
            end = start + 0.1

        entries.append(
            SubtitleEntry(
                index=len(entries) + 1,
                start=format_srt_timestamp(start),
                end=format_srt_timestamp(end),
                text=text,
            )
        )
        emit_status(
            f"Recognized {len(entries)} subtitle segments..."
        )

    if not entries:
        raise ValueError("No speech segments were detected in this media file.")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    emit_status("Writing SRT file...")
    write_srt(target_path, entries)

    return TranscriptionResult(
        detected_language=str(getattr(info, "language", "") or language or "unknown"),
        segment_count=len(entries),
        duration_seconds=getattr(info, "duration", None),
    )


def format_srt_timestamp(total_seconds: float) -> str:
    milliseconds = max(0, int(round(total_seconds * 1000)))
    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000
    minutes = milliseconds // 60_000
    milliseconds %= 60_000
    seconds = milliseconds // 1000
    milliseconds %= 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def _should_fallback_to_cpu(device: str, exc: RuntimeError) -> bool:
    if device not in ("auto", "cuda"):
        return False

    message = str(exc).lower()
    markers = (
        "cublas",
        "cudnn",
        "cuda",
        "cannot be loaded",
        "not found",
    )
    return any(marker in message for marker in markers)
