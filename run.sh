#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
echo "Starting Voice2Clip..."
echo "Press Ctrl+C to stop manually."
python src/main.py
