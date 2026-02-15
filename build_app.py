"""
Build Voice2Clip as a macOS .app bundle using PyInstaller.

Usage:
    uv run python build_app.py
"""

import subprocess
import sys


def build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "Voice2Clip",
        "--noconfirm",          # Overwrite output directory without asking
        "--windowed",           # .app bundle, no terminal
        "--onedir",             # faster builds, easier to debug
        "--add-data", "icon.png:.",
        "--add-data", "src/icons:src/icons",
        "--paths", "src",
        "--hidden-import", "history",
        "--hidden-import", "recorder",
        "--hidden-import", "sounds",
        "--hidden-import", "transcriber",
        "--hidden-import", "rumps",
        "--hidden-import", "pynput",
        "--hidden-import", "pynput.keyboard",
        "--hidden-import", "pynput.keyboard._darwin",
        "--hidden-import", "pyperclip",
        "--hidden-import", "pyperclip",
        "--hidden-import", "google.genai",
        "--hidden-import", "hotkey_handler",
        "--hidden-import", "Quartz",
        "--osx-bundle-identifier", "com.enrique.voice2clip.pro",
        "src/main.py",
    ]
    subprocess.run(cmd, check=True)

    # Inject Permissions into Info.plist
    plist_path = "dist/Voice2Clip.app/Contents/Info.plist"
    print(f"🔧 Injecting permissions into {plist_path}...")
    
    perms = [
        ("NSMicrophoneUsageDescription", "Voice2Clip needs access to microphone to record audio."),
        ("NSSpeechRecognitionUsageDescription", "Voice2Clip needs speech recognition to transcribe audio.")
    ]

    for key, value in perms:
        subprocess.run([
            "/usr/libexec/PlistBuddy", 
            "-c", 
            f"Add :{key} string '{value}'", 
            plist_path
        ], check=False) # check=False in case key exists (though dist is fresh)

    # Sign with Entitlements (Ad-hoc)
    print("✍️  Signing with entitlements...")
    subprocess.run([
        "codesign",
        "--force",
        "--deep",
        "--sign", "-",
        "--entitlements", "entitlements.plist",
        "dist/Voice2Clip.app"
    ], check=True)

    print("\n✅ Built & Signed! App is at: dist/Voice2Clip.app")


if __name__ == "__main__":
    build()
