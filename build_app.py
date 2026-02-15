"""
Build Voice2Clip as a macOS .app bundle using PyInstaller.

Usage:
    uv run python build_app.py
"""

import subprocess
import sys


def build():
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "Voice2Clip.spec"]
    subprocess.run(cmd, check=True)

    # Inject Permissions into Info.plist
    plist_path = "dist/Voice2Clip.app/Contents/Info.plist"
    print(f"🔧 Injecting permissions into {plist_path}...")

    perms = [
        ("NSMicrophoneUsageDescription", "Voice2Clip needs access to microphone to record audio."),
        (
            "NSSpeechRecognitionUsageDescription",
            "Voice2Clip needs speech recognition to transcribe audio.",
        ),
    ]

    for key, value in perms:
        subprocess.run(
            ["/usr/libexec/PlistBuddy", "-c", f"Add :{key} string '{value}'", plist_path],
            check=False,
        )  # check=False in case key exists (though dist is fresh)

    # Sign with Entitlements (Ad-hoc)
    print("✍️  Signing with entitlements...")
    subprocess.run(
        [
            "codesign",
            "--force",
            "--deep",
            "--sign",
            "-",
            "--entitlements",
            "entitlements.plist",
            "dist/Voice2Clip.app",
        ],
        check=True,
    )

    print("\n✅ Built & Signed! App is at: dist/Voice2Clip.app")


if __name__ == "__main__":
    build()
