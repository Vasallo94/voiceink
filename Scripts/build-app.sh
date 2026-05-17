#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="VoiceInk"
PRODUCT_NAME="VoiceInk"
BUNDLE_ID="com.enrique.voiceink"
APP_DIR="$ROOT_DIR/dist/$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
EXECUTABLE="$ROOT_DIR/.build/release/$PRODUCT_NAME"

cd "$ROOT_DIR"

swift build -c release --product "$PRODUCT_NAME"

rm -rf "$ROOT_DIR/dist"
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

cp "$EXECUTABLE" "$MACOS_DIR/$APP_NAME"
chmod 755 "$MACOS_DIR/$APP_NAME"

if [ -f "$ROOT_DIR/icon.icns" ]; then
    cp "$ROOT_DIR/icon.icns" "$RESOURCES_DIR/icon.icns"
fi

cat > "$CONTENTS_DIR/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleDisplayName</key>
    <string>VoiceInk</string>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIconFile</key>
    <string>icon</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>VoiceInk</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>0.1.0</string>
    <key>CFBundleVersion</key>
    <string>0.1.0</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.productivity</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSMicrophoneUsageDescription</key>
    <string>VoiceInk needs microphone access to record audio for transcription.</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>
PLIST

codesign --force --deep --sign - "$APP_DIR"
codesign --verify --deep --strict "$APP_DIR"

echo "Built $APP_DIR"
