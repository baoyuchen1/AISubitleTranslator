# AI Subtitle Translator

A Windows-focused desktop tool for:

- transcribing video or audio into `.srt`
- translating subtitle files with your own LLM API
- live game subtitle OCR translation with an overlay

## Features

- Local video/audio transcription with `faster-whisper`
- OpenAI-compatible subtitle translation API
- Real-time OCR translation overlay for games
- GUI workflow for daily use
- Windows batch launcher
- PyInstaller packaging for `.exe` builds

## Privacy

- Speech transcription runs locally and does not consume LLM API tokens
- Your real API credentials are expected to live in `.env`
- `.env`, logs, build output, and virtual environments are ignored by git

## Project Structure

```text
src/ai_subtitle/
  cli.py
  config.py
  game_ocr.py
  gui.py
  overlay.py
  subtitles.py
  transcribe.py
  video_pipeline.py
  providers/
    base.py
    openai_compatible.py
```

## Quick Start

1. Create a virtual environment
2. Install dependencies
3. Copy `.env.example` to `.env`
4. Launch the GUI

### Windows

```powershell
py -3.9 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
Copy-Item .env.example .env
python launch_gui.pyw
```

Or just use:

- `launch_gui.bat`

## GUI Workflows

### 1. Video or Audio to Subtitle

- Choose a media file
- Choose an output `.srt`
- Select a Whisper model
- Click `Generate Subtitle From Video`

### 2. Translate Existing Subtitle

- Choose an input `.srt`
- Choose an output `.srt`
- Configure target language
- Click `Start Translation`

### 3. Live Game OCR

- Set the subtitle region
- Start OCR translation
- Read translated text from the overlay window

## Whisper Models

Typical tradeoff:

- `tiny` / `base`: fastest, lowest accuracy
- `small`: good default balance
- `medium`: higher quality, slower
- `large-v3`: strongest quality, highest resource usage

## Packaging

See:

- [PACKAGING.md](./PACKAGING.md)

Quick command:

- `build_exe.bat`

## Git Safety

Sensitive local files are intentionally excluded:

- `.env`
- `ai_subtitle.log`
- `.venv/`
- `build/`
- `dist/`

## Limitations

- First Whisper model load may download model files
- OCR quality depends on subtitle position, font, and background clarity
- This project currently focuses on Windows desktop usage

## Contributing

See:

- [CONTRIBUTING.md](./CONTRIBUTING.md)

## Security

If you find a security or credential-handling issue, see:

- [SECURITY.md](./SECURITY.md)

## License

This project is released under the MIT License.
