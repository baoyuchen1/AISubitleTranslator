from __future__ import annotations

import audioop
from dataclasses import dataclass
import tempfile
from pathlib import Path
import wave
from typing import Callable, Optional, Union

import numpy as np

from ai_subtitle.subtitles import SubtitleEntry, write_srt

PROFILE_BALANCED = "balanced"
PROFILE_HIGH_QUALITY = "high_quality"
PROFILE_NOISY_SCENE = "noisy_scene"


@dataclass
class TranscriptionResult:
    detected_language: str
    segment_count: int
    duration_seconds: Optional[float]


@dataclass
class TranscriptionSettings:
    model_size: str
    beam_size: int
    vad_filter: bool
    preprocess_audio: bool
    profile: str


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
    preprocess_audio: bool = False,
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
    transcribe_path = source_path
    temporary_audio_path: Optional[Path] = None

    if not source_path.exists():
        raise FileNotFoundError(f"Input media file not found: {source_path}")

    try:
        if preprocess_audio:
            emit_status("Preprocessing audio for speech clarity...")
            try:
                temporary_audio_path = _preprocess_media_audio(source_path, emit_status)
            except Exception as exc:
                emit_status(
                    "Audio preprocessing failed. Continuing with original audio stream. "
                    f"Reason: {exc}"
                )
            else:
                transcribe_path = temporary_audio_path
                emit_status("Audio cleanup finished. Starting transcription from cleaned audio...")

        active_device = device
        active_compute_type = _normalize_compute_type(device, compute_type, emit_status)

        try:
            emit_status(
                f"Loading Whisper model on {active_device}. First run may take a while if the model needs to be downloaded."
            )
            model = WhisperModel(model_size, device=active_device, compute_type=active_compute_type)
            emit_status("Whisper model ready. Starting transcription...")
            segments, info = model.transcribe(
                str(transcribe_path),
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
            active_compute_type = _normalize_compute_type(active_device, compute_type, emit_status)
            model = WhisperModel(model_size, device=active_device, compute_type=active_compute_type)
            emit_status("CPU Whisper model ready. Restarting transcription...")
            segments, info = model.transcribe(
                str(transcribe_path),
                language=None if not language or language.lower() == "auto" else language,
                task="transcribe",
                beam_size=beam_size,
                vad_filter=vad_filter,
                condition_on_previous_text=True,
            )
        except ValueError as exc:
            if not _should_fallback_compute_type(active_device, active_compute_type, exc):
                raise

            emit_status(
                f"Compute type {active_compute_type} is not supported on {active_device}. Falling back to int8."
            )
            active_compute_type = "int8"
            model = WhisperModel(model_size, device=active_device, compute_type=active_compute_type)
            emit_status("Fallback Whisper model ready. Restarting transcription...")
            segments, info = model.transcribe(
                str(transcribe_path),
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
    finally:
        if temporary_audio_path is not None:
            try:
                temporary_audio_path.unlink(missing_ok=True)
            except OSError:
                pass


def resolve_transcription_settings(
    *,
    model_size: str,
    profile: str,
) -> TranscriptionSettings:
    normalized_profile = (profile or PROFILE_BALANCED).strip().lower().replace(" ", "_")
    if normalized_profile not in (
        PROFILE_BALANCED,
        PROFILE_HIGH_QUALITY,
        PROFILE_NOISY_SCENE,
    ):
        normalized_profile = PROFILE_BALANCED

    effective_model = model_size.strip() or "small"
    if normalized_profile in (PROFILE_HIGH_QUALITY, PROFILE_NOISY_SCENE):
        effective_model = _upgrade_model_for_quality(effective_model)

    if normalized_profile == PROFILE_HIGH_QUALITY:
        return TranscriptionSettings(
            model_size=effective_model,
            beam_size=8,
            vad_filter=True,
            preprocess_audio=False,
            profile=normalized_profile,
        )

    if normalized_profile == PROFILE_NOISY_SCENE:
        return TranscriptionSettings(
            model_size=effective_model,
            beam_size=8,
            vad_filter=True,
            preprocess_audio=True,
            profile=normalized_profile,
        )

    return TranscriptionSettings(
        model_size=effective_model,
        beam_size=5,
        vad_filter=True,
        preprocess_audio=False,
        profile=PROFILE_BALANCED,
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


def _should_fallback_compute_type(device: str, compute_type: str, exc: ValueError) -> bool:
    message = str(exc).lower()
    if "compute type" not in message:
        return False
    if device not in ("cpu", "auto", "cuda"):
        return False
    return compute_type != "int8"


def _normalize_compute_type(
    device: str,
    compute_type: str,
    emit_status: Callable[[str], None],
) -> str:
    normalized = (compute_type or "int8").strip().lower()
    if device == "cpu" and normalized in ("int8_float16", "float16"):
        emit_status(
            f"Compute type {normalized} is not suitable for CPU. Using int8 instead."
        )
        return "int8"
    return normalized or "int8"


def _upgrade_model_for_quality(model_size: str) -> str:
    order = {
        "tiny": 0,
        "base": 1,
        "small": 2,
        "medium": 3,
        "large-v3": 4,
    }
    normalized = model_size.strip().lower()
    if order.get(normalized, 2) < order["medium"]:
        return "medium"
    return model_size.strip() or "medium"


def _preprocess_media_audio(
    source_path: Path,
    emit_status: Callable[[str], None],
) -> Path:
    try:
        import av
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: PyAV. Rebuild or reinstall the app dependencies."
        ) from exc

    output_file = tempfile.NamedTemporaryFile(prefix="ai_subtitle_clean_", suffix=".wav", delete=False)
    output_path = Path(output_file.name)
    output_file.close()

    pcm = bytearray()
    try:
        with av.open(str(source_path)) as container:
            audio_stream = next((stream for stream in container.streams if stream.type == "audio"), None)
            if audio_stream is None:
                raise ValueError("No audio stream was found in this media file.")

            resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
            decoded_frames = 0
            for packet in container.demux(audio_stream):
                for frame in packet.decode():
                    decoded_frames += 1
                    for resampled_frame in _ensure_frame_list(resampler.resample(frame)):
                        pcm.extend(_frame_to_pcm_bytes(resampled_frame))
                    if decoded_frames % 120 == 0:
                        emit_status(f"Preprocessing audio... decoded {decoded_frames} frames")

            for resampled_frame in _ensure_frame_list(resampler.resample(None)):
                pcm.extend(_frame_to_pcm_bytes(resampled_frame))
    except Exception:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    if not pcm:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise ValueError("Unable to extract usable audio samples from this media file.")

    emit_status("Applying speech cleanup and level normalization...")
    cleaned_pcm = _clean_audio_pcm(bytes(pcm))
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(cleaned_pcm)

    return output_path


def _ensure_frame_list(resampled) -> list:
    if resampled is None:
        return []
    if isinstance(resampled, list):
        return resampled
    return [resampled]


def _frame_to_pcm_bytes(frame) -> bytes:
    array = frame.to_ndarray()
    return np.asarray(array, dtype=np.int16).tobytes()


def _clean_audio_pcm(pcm: bytes) -> bytes:
    if not pcm:
        return pcm

    width = 2
    global_rms = audioop.rms(pcm, width)
    target_rms = 3500
    gain = min(3.0, max(0.8, float(target_rms) / max(global_rms, 1)))
    normalized = audioop.mul(pcm, width, gain)

    chunk_size = 640
    gate_threshold = max(180, int(global_rms * 0.35))
    cleaned_parts = []
    for offset in range(0, len(normalized), chunk_size):
        chunk = normalized[offset : offset + chunk_size]
        if not chunk:
            continue
        if audioop.rms(chunk, width) < gate_threshold:
            chunk = audioop.mul(chunk, width, 0.12)
        cleaned_parts.append(chunk)

    cleaned = b"".join(cleaned_parts)
    return audioop.mul(cleaned, width, 1.08)
