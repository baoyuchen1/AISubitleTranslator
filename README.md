# AI Subtitle Translator

A Windows desktop tool for:

- transcribing video or audio into `.srt`
- translating `.srt` subtitles with your own LLM API
- live game subtitle OCR translation

## Main Features

- local `faster-whisper` transcription
- OpenAI-compatible translation API
- game OCR overlay translation
- GUI launcher for daily use
- Windows batch launcher and PyInstaller packaging

## Run

Use:

- `launch_gui.bat`

## Build EXE

Use:

- `build_exe.bat`

## Notes

- `.env`, logs, build output, and virtual environments are ignored by git.
- the transcription step runs locally and does not consume LLM API tokens
