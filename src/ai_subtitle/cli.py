from __future__ import annotations

import argparse
import sys

from ai_subtitle.config import load_config
from ai_subtitle.game_ocr import GameOCRTranslator, ScreenRegion
from ai_subtitle.providers.openai_compatible import OpenAICompatibleProvider
from ai_subtitle.transcribe import resolve_transcription_settings, transcribe_media_to_srt
from ai_subtitle.video_pipeline import translate_srt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-subtitle",
        description="Translate video subtitles and game subtitles with your own LLM API.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    srt_parser = subparsers.add_parser(
        "translate-srt",
        help="Translate an existing SRT subtitle file.",
    )
    srt_parser.add_argument("--input", required=True, help="Input SRT path.")
    srt_parser.add_argument("--output", required=True, help="Output SRT path.")
    srt_parser.add_argument(
        "--target-language",
        default="Simplified Chinese",
        help="Target language, for example Simplified Chinese or English.",
    )
    srt_parser.add_argument(
        "--bilingual",
        action="store_true",
        help="Keep original and translated lines together.",
    )
    srt_parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of subtitle lines sent to the model per request.",
    )

    transcribe_parser = subparsers.add_parser(
        "transcribe-video",
        help="Transcribe a video or audio file into an SRT subtitle file.",
    )
    transcribe_parser.add_argument("--input", required=True, help="Input video/audio path.")
    transcribe_parser.add_argument("--output", required=True, help="Output SRT path.")
    transcribe_parser.add_argument(
        "--model-size",
        default="small",
        help="Whisper model size, for example tiny, base, small, medium, or large-v3.",
    )
    transcribe_parser.add_argument(
        "--profile",
        default="balanced",
        help="Recognition profile: balanced, high_quality, or noisy_scene.",
    )
    transcribe_parser.add_argument(
        "--language",
        default="auto",
        help="Speech language code such as ja, en, zh, or auto.",
    )
    transcribe_parser.add_argument(
        "--device",
        default="auto",
        help="Inference device: auto, cpu, or cuda.",
    )
    transcribe_parser.add_argument(
        "--compute-type",
        default="int8",
        help="Inference compute type such as int8, float16, or float32.",
    )
    transcribe_parser.add_argument(
        "--beam-size",
        type=int,
        default=5,
        help="Beam size used during transcription.",
    )
    transcribe_parser.add_argument(
        "--no-vad-filter",
        action="store_true",
        help="Disable VAD filtering.",
    )

    game_parser = subparsers.add_parser(
        "game-ocr",
        help="OCR a subtitle region and translate it in real time.",
    )
    game_parser.add_argument(
        "--region",
        required=True,
        help="Subtitle region as left,top,width,height.",
    )
    game_parser.add_argument(
        "--target-language",
        default="Simplified Chinese",
        help="Target language, for example Simplified Chinese or English.",
    )
    game_parser.add_argument(
        "--interval",
        type=float,
        default=0.8,
        help="Seconds between OCR scans.",
    )
    game_parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.92,
        help="Skip translation when OCR text is too similar to the last one.",
    )

    return parser


def parse_region(value: str) -> ScreenRegion:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4:
        raise ValueError("Region must be left,top,width,height.")

    left, top, width, height = [int(part) for part in parts]
    return ScreenRegion(left=left, top=top, width=width, height=height)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "translate-srt":
            config = load_config()
            provider = OpenAICompatibleProvider(config)
            translate_srt(
                args.input,
                args.output,
                provider=provider,
                target_language=args.target_language,
                bilingual=args.bilingual,
                batch_size=args.batch_size,
            )
            print(f"Translated subtitle written to: {args.output}")
            return 0

        if args.command == "transcribe-video":
            settings = resolve_transcription_settings(
                model_size=args.model_size,
                profile=args.profile,
            )
            result = transcribe_media_to_srt(
                args.input,
                args.output,
                model_size=settings.model_size,
                language=args.language,
                device=args.device,
                compute_type=args.compute_type,
                beam_size=settings.beam_size if args.beam_size == 5 else args.beam_size,
                vad_filter=settings.vad_filter if not args.no_vad_filter else False,
                preprocess_audio=settings.preprocess_audio,
            )
            print(
                "Transcribed subtitle written to: "
                f"{args.output} "
                f"(language={result.detected_language}, segments={result.segment_count})"
            )
            return 0

        if args.command == "game-ocr":
            config = load_config()
            provider = OpenAICompatibleProvider(config)
            translator = GameOCRTranslator(
                provider=provider,
                target_language=args.target_language,
                region=parse_region(args.region),
                interval_seconds=args.interval,
                similarity_threshold=args.similarity_threshold,
            )
            translator.run()
            return 0

        parser.print_help()
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
