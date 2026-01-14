# Voice2Clip 🎙️

A macOS menu bar utility that records voice, transcribes it with Google Gemini (cleaning up filler words), and copies clean text to your clipboard.

## Features
- **Global Hotkey**: `⌘+Shift+D` to start/stop recording
- **Silence Detection**: Auto-stops after 3 seconds of silence
- **AI-Powered Cleanup**: Removes "ehm", "uh", fixes punctuation via Gemini 3 Flash
- **Instant Clipboard**: Paste anywhere with `⌘+V`

## Quick Start
```bash
# 1. Set your API key
echo "GOOGLE_API_KEY=your_key_here" > .env

# 2. Run
./run.sh
```

## Requirements
- macOS with Accessibility permissions for your Terminal
- Google AI Studio API Key ([get one here](https://aistudio.google.com/app/apikey))
- Python 3.12+ (managed by `uv`)

## Tech Stack
`rumps` · `pyaudio` · `google-genai` · `pynput`
