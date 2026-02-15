#!/bin/bash

# Voice2Clip Installer

APP_NAME="Voice2Clip.app"
DIST_DIR="dist"
INSTALL_DIR="/Applications"
SOURCE_APP="$DIST_DIR/$APP_NAME"
DEST_APP="$INSTALL_DIR/$APP_NAME"

echo "🚀 Starting Voice2Clip Installation..."

# 0. Close running instances
echo "🛑 Closing running instances..."
pkill -f "Voice2Clip" || true
pkill -f "main.py" || true

# 1. Build the application
echo "📦 Building Application with PyInstaller..."
uv run build_app.py

if [ ! -d "$SOURCE_APP" ]; then
    echo "❌ Build failed. $SOURCE_APP not found."
    exit 1
fi

# 2. Install to /Applications
echo "📂 Installing to $INSTALL_DIR..."
if [ -d "$DEST_APP" ]; then
    echo "   Removing existing version..."
    rm -rf "$DEST_APP"
fi

mv "$SOURCE_APP" "$INSTALL_DIR"

if [ -d "$DEST_APP" ]; then
    echo "✅ Successfully installed to $DEST_APP"
else
    echo "❌ Installation failed."
    exit 1
fi

# 2.5 Copy Configuration
echo "⚙️  Copying configuration to ~/.voice2clip.env..."
if [ -f ".env" ]; then
    cp ".env" "$HOME/.voice2clip.env"
    echo "✅ Configuration saved."
else
    echo "⚠️  WARNING: .env file not found. App may not work without API Key."
fi

# 3. Cleanup
echo "🧹 Cleaning up build artifacts..."
rm -rf "build" "$DIST_DIR" "$APP_NAME.spec"

# 4. Post-Install Instructions
echo ""
echo "🎉 Installation Complete!"
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo ""
echo "1. ACCESSIBILITY PERMISSIONS:"
echo "   I will open System Settings for you."
echo "   - If Voice2Clip is already in the list: REMOVE IT (-) and ADD IT (+) again."
echo "   - Make sure the toggle is ON."
echo ""
echo "2. START AT LOGIN:"
echo "   I will open Login Items settings."
echo "   - Click '+' and select Voice2Clip from Applications."
echo ""

read -p "Press Enter to open System Settings and launch the app..."

# Open System Settings
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
open "x-apple.systempreferences:com.apple.LoginItems-Settings.extension"

# Launch the app
echo "🚀 Launching Voice2Clip..."
open "$DEST_APP"

echo ""
echo "Done. You should see the Voice2Clip icon in your menu bar."
