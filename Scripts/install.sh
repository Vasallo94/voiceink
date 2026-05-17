#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="VoiceInk.app"
SOURCE_APP="$ROOT_DIR/dist/$APP_NAME"
DEST_APP="/Applications/$APP_NAME"

cd "$ROOT_DIR"

echo "Building VoiceInk..."
bash Scripts/build-app.sh

if [ ! -d "$SOURCE_APP" ]; then
    echo "Build failed: $SOURCE_APP was not created."
    exit 1
fi

echo "Stopping running VoiceInk instances..."
pkill -f VoiceInk || true
sleep 1

echo "Installing to $DEST_APP..."
rm -rf "$DEST_APP"
ditto "$SOURCE_APP" "$DEST_APP"

codesign --verify --deep --strict "$DEST_APP"

if [ -f "$ROOT_DIR/.env" ] && [ ! -f "$HOME/.voiceink.env" ]; then
    cp "$ROOT_DIR/.env" "$HOME/.voiceink.env"
    chmod 600 "$HOME/.voiceink.env"
    echo "Copied .env to ~/.voiceink.env"
elif [ -f "$HOME/.voice2clip.env" ] && [ ! -f "$HOME/.voiceink.env" ]; then
    cp "$HOME/.voice2clip.env" "$HOME/.voiceink.env"
    chmod 600 "$HOME/.voiceink.env"
    echo "Copied ~/.voice2clip.env to ~/.voiceink.env"
fi

echo "Launching VoiceInk from /Applications..."
open -n "$DEST_APP"

echo ""
echo "Installed: $DEST_APP"
echo "If auto-paste does not work, enable /Applications/VoiceInk.app in System Settings > Privacy & Security > Accessibility."
