# Voice2Clip 🎙️

A macOS menu bar utility that records voice, transcribes it with Google Gemini (cleaning up filler words), and copies clean text to your clipboard.

## Features
- **Global Hotkey**: `Ctrl+Shift+S` by default (configurable via `VOICE2CLIP_CARBON_HOTKEY`)
- **Silence Detection**: Auto-stops after 5 seconds of silence
- **Smart Transcription**: Removes "ehm", "uh" & formats instructions using **Gemini 2.5 Flash**
- **History**: Access last 50 transcriptions from the menu bar
- **Feedback**: Native system sounds for start/stop/error

## Installation (Recommended)
This installs the app to `/Applications` and configures it for daily use:

```bash
# 1. Set your API key
cp .env.example .env
# edit .env and set GOOGLE_API_KEY

# 2. Run the installer
./install.sh
```
*Follow the on-screen instructions to grant Microphone (and optionally Accessibility) permissions.*

## Development
```bash
# Run from source
./run.sh

# Install dev tooling
uv sync --group dev

# Run quality checks
uv run ruff check .
uv run pyright
uv run pytest -q

# Enable git hooks
uv run pre-commit install

# Run hooks manually
uv run pre-commit run --all-files
```

## Requirements
- macOS 12+
- Google AI Studio API Key ([get one here](https://aistudio.google.com/app/apikey))
- Python 3.12+ (managed by `uv`)

## Privacy & Retention
- `VOICE2CLIP_PERSIST_MODE=normal|memory` (`memory` stores temp audio in `/tmp`)
- `VOICE2CLIP_HISTORY_ENABLED=true|false`
- `VOICE2CLIP_HISTORY_MAX_ITEMS=50` (default)
- `VOICE2CLIP_HISTORY_RETENTION_DAYS=0` (`0` disables day-based pruning)
- `VOICE2CLIP_AUDIO_RETENTION=delete|keep` (`delete` is default)

## macOS Permissions
- **Microphone**: required to record audio for transcription.
- **Accessibility**: optional fallback if Carbon hotkey registration is unavailable.

## Tech Stack
`PySide6` · `pyaudio` · `google-genai` · `pyperclip` · `pyinstaller`

## Release Checklist
```bash
# 1) Run quality gates
uv run pre-commit run --all-files
uv run pytest -q

# 2) Build app (single source of truth: Voice2Clip.spec)
uv run python build_app.py

# 3) Smoke-test app bundle
open dist/Voice2Clip.app
```

- Verify microphone permission prompt appears on first recording.
- Verify the configured global hotkey toggles recording.
- Verify start/stop/transcribe/copy flow works in the packaged app.

