# Changelog

All notable changes to this project will be documented in this file.

## 0.2.0 - 2026-04-18

### Added

- Added a Windows-friendly GUI workflow for subtitle transcription, translation, and live game OCR translation.
- Added automatic video or audio to `.srt` transcription with local `faster-whisper`.
- Added recognition profiles for `Balanced`, `High Quality`, and `Noisy Scene` transcription modes.
- Added local audio preprocessing for noisy scenes before Whisper transcription.
- Added a task progress window with live logs, progress feedback, and a pixel-art loading animation.
- Added richer pixel animation details including day and night cycling plus roaming grassland background elements.
- Added direct `Play Video` and `Open Folder` actions in the video workflow.
- Added configurable subtitle display duration controls for the game OCR overlay.
- Added packaging and public repository files: `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, and repository-safe defaults.

### Changed

- Improved Whisper runtime fallback behavior for CPU and compute-type compatibility.
- Improved task visibility by surfacing active recognition settings in the progress log.
- Improved README and packaging documentation for public GitHub use.
- Updated dependency declarations to include `PyAV` and `numpy` for noisy-scene preprocessing.

### Fixed

- Fixed cases where transcription actions appeared unresponsive by adding visible task progress and logging.
- Fixed noisy-scene preprocessing failures from interrupting the whole transcription flow by falling back to the original audio stream.
- Fixed packaging coverage so audio preprocessing dependencies are included in the PyInstaller build.
