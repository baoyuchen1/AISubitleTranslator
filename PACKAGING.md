# Packaging

## Double-click launcher

If Python and dependencies are already installed, use:

- `launch_gui.bat`

It tries these in order:

1. `.venv\Scripts\pythonw.exe`
2. `pyw -3`
3. `pythonw`

## Build EXE

Double-click:

- `build_exe.bat`

What it does:

1. Creates `.venv` if missing
2. Installs the project, `pyinstaller`, and the local speech recognition dependency stack
3. Builds a windowed executable with `AI_Subtitle_Translator.spec`

Expected output:

- `dist\AI Subtitle Translator\AI Subtitle Translator.exe`

## Notes

- The EXE still needs network access to call your model API.
- Video-to-SRT transcription runs locally with `faster-whisper`, so first launch may download the selected Whisper model unless it is already cached.
- Your `.env` file stays next to the EXE or project root, depending on how you run it.
- If `rapidocr-onnxruntime` or `faster-whisper` pulls in extra runtime files on your machine, the spec file is the place to extend hidden imports, binaries, or data collection.
