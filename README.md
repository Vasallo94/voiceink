# VoiceInk

**Dictate into any macOS app — press a hotkey, speak, and your words land where the cursor is.**

VoiceInk is a native menu-bar dictation app. Hit `Ctrl+Shift+S`, talk, and when you stop it transcribes
with Gemini and auto-pastes the text straight into whatever app has focus — no window to switch to, no
copy-paste dance. I built it to scratch my own itch and now use it every day.

It's also my hands-on way to learn Swift / AppKit: a small, real, daily-driver app rather than a tutorial.

> **Status: early alpha** — the core dictation loop is solid and in daily use. Next up: a model/engine
> selector, fully on-device transcription with local Whisper (no audio leaves your Mac), and auto-stop on silence.

## Features

- Native AppKit menu bar app.
- Global `Ctrl+Shift+S` hotkey to start and stop recording.
- Microphone recording via AVFoundation.
- Gemini transcription via `URLSession`.
- Auto-copy and auto-paste into the focused text field.
- Menu bar SF Symbol icon with idle/recording state.
- Manual stop mode by default.
- Settings foundation for future auto-stop after silence.

## Requirements

- macOS 13+
- Swift 6 toolchain / Xcode Command Line Tools
- Google AI Studio API key

## Configuration

Create a local environment file:

```bash
cp .env.example ~/.voiceink.env
```

Then edit `~/.voiceink.env`:

```bash
GOOGLE_API_KEY=your_google_api_key_here
```

You can also add the Gemini key from `Settings...` in the menu bar app. Keys saved from the app are stored in the macOS Keychain. The environment file is kept as a local fallback for development.

## Build

```bash
Scripts/check.sh
swift run VoiceInkCoreSmokeTests
swift build --product VoiceInk
bash Scripts/build-app.sh
```

The app bundle is created at:

```text
dist/VoiceInk.app
```

## Run

```bash
open dist/VoiceInk.app
```

## Install Locally

```bash
Scripts/install.sh
```

This installs VoiceInk to:

```text
/Applications/VoiceInk.app
```

Using a stable `/Applications` path helps macOS keep Microphone and Accessibility permissions attached to the right app.

## Quality

```bash
Scripts/format.sh
Scripts/check.sh
```

`Scripts/check.sh` runs `swift-format` in strict lint mode, the smoke test executable, and the app build.

## Permissions

VoiceInk needs:

- **Microphone** to record audio.
- **Accessibility** to auto-paste the final transcript into the app that currently has focus.

If auto-paste does not work, open the menu bar icon and choose `Request Paste Permission`, then enable `VoiceInk.app` in System Settings.

## Privacy

- API keys saved in the app are stored in the macOS Keychain.
- Recordings are written to a temporary WAV file and overwritten on the next recording.
- Transcription currently uses Gemini, so audio is sent to Google's API when you stop recording.
- VoiceInk does not include analytics or telemetry.

## Roadmap

- Auto-stop after configurable silence.
- Engine/model selector:
  - Gemini API
  - OpenAI transcription models
  - Local Whisper
- Richer settings popover.

## License

MIT. See [LICENSE](LICENSE).
