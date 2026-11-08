#!/usr/bin/env bash
# Quick launcher for Faceless AI Shorts Engine

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run initial setup."
    exit 1
fi

source venv/bin/activate
python make_video.py "$@"

