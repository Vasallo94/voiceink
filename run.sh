#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Voice2Clip..."
echo "Press Ctrl+C to stop manually."
uv run src/main.py
