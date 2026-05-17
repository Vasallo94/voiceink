#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"
swift format lint --recursive --parallel --strict --configuration .swift-format Sources
swift run VoiceInkCoreSmokeTests
swift build --product VoiceInk
