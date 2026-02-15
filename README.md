# Voice2Clip 🎙️

A macOS menu bar utility that records voice, transcribes it with Google Gemini (cleaning up filler words), and copies clean text to your clipboard.

## Features
- **Global Hotkey**: `Cmd+Option+R` (⌘+⌥+R) to start/stop recording (Required: Accessibility permissions)
- **Silence Detection**: Auto-stops after 3 seconds of silence
- **Smart Transcription**: Removes "ehm", "uh" & formats instructions using **Gemini 2.5 Flash Lite**
- **History**: Access last 50 transcriptions from the menu bar
- **Feedback**: Native system sounds for start/stop/error

## Installation (Recommended)
This installs the app to `/Applications` and configures it for daily use:

```bash
# 1. Set your API key
echo "GOOGLE_API_KEY=your_key_here" > .env

# 2. Run the installer
./install.sh
```
*Follow the on-screen instructions to grant Accessibility & Login Item permissions.*

## Development
```bash
# Run from source
./run.sh
```

## Requirements
- macOS 12+
- Google AI Studio API Key ([get one here](https://aistudio.google.com/app/apikey))
- Python 3.12+ (managed by `uv`)

## Tech Stack
`rumps` · `pyaudio` · `google-genai` · `pynput` · `pyinstaller`

