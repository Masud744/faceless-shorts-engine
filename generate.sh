#!/usr/bin/env bash
# ==============================================================================
# Faceless Shorts Engine - 1-Click Pipeline Automation Runner
# Usage: ./generate.sh <style> <project-name>
# Available styles: deep-dive, tall-tale, inside-out, stick-story, night-file, paper-atlas
# ==============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"

if [ $# -lt 2 ]; then
  echo "Usage: ./generate.sh <style> <project-name>"
  echo "Styles available:"
  for s in "$ROOT_DIR"/faceless-shorts/styles/*/; do
    echo "  - $(basename "$s")"
  done
  exit 1
fi

STYLE="$1"
NAME="$2"
shift 2

TOPIC=""
LANG="en"
VOICE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --topic) TOPIC="$2"; shift 2 ;;
    --lang) LANG="$2"; shift 2 ;;
    --voice) VOICE="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

PROJECT_DIR="$ROOT_DIR/projects/$NAME"

# Activate Python Virtual Environment
if [ -d "$ROOT_DIR/venv" ]; then
  source "$ROOT_DIR/venv/bin/activate"
fi

echo "======================================================================"
echo "Starting video generation: Style '$STYLE', Project '$NAME'"
if [ -n "$TOPIC" ]; then
  echo "Topic: '$TOPIC' (Language: $LANG)"
fi
echo "======================================================================"

# Step 1: Scaffold project if it doesn't already exist
if [ ! -d "$PROJECT_DIR" ]; then
  echo "[1/6] Scaffolding new project from template..."
  bash "$ROOT_DIR/faceless-shorts/scripts/new_video.sh" "$STYLE" "$NAME" --dir "$ROOT_DIR/projects"
else
  echo "[1/6] Project '$NAME' already exists in projects/. Using existing files."
fi

# Step 1.5: If topic is provided, generate viral AI script with Groq
if [ -n "$TOPIC" ]; then
  echo "[AI] Generating high-retention script with Groq AI..."
  EXTRA_ARGS=()
  [ -n "$VOICE" ] && EXTRA_ARGS+=(--voice "$VOICE")
  python "$ROOT_DIR/engine/ai_script.py" --topic "$TOPIC" --style "$STYLE" --lang "$LANG" "${EXTRA_ARGS[@]}" --out "$PROJECT_DIR/script.json"
fi

# Step 2: Synthesize neural voiceover
echo "[2/6] Generating voice narration with Kokoro-82M TTS..."
python "$ROOT_DIR/faceless-shorts/scripts/voice.py" "$PROJECT_DIR"

# Step 3: Whisper word-level timestamp alignment
echo "[3/6] Aligning word timestamps with faster-whisper..."
python "$ROOT_DIR/faceless-shorts/scripts/words.py" "$PROJECT_DIR"

# Step 3.5: Dynamic 3D Scene Mapping Engine
echo "[3.5/6] Dynamically mapping script lines to 3D scenes & shots..."
python "$ROOT_DIR/engine/scene_mapper.py" "$PROJECT_DIR" --style "$STYLE"

# Step 4: Extract sound markers and mix audio
echo "[4/6] Extracting cues and generating procedural audio mix..."
cd "$PROJECT_DIR"
node tools/capture.mjs cues
python tools/mix.py .

# Step 5: Render visual QA contact sheet
echo "[5/6] Rendering QA contact sheet..."
node tools/capture.mjs sheet review/all.jpg 3 4

# Step 6: Render master MP4 video
echo "[6/6] Rendering full 1080x1920 video via Headless Chrome & FFmpeg..."
QS='&res=0.7&aa=2' FPS=24 node tools/capture.mjs video "renders/${NAME}.mp4"

echo "======================================================================"
echo "Video generation complete!"
echo "Master MP4: $PROJECT_DIR/renders/${NAME}.mp4"
echo "Review Sheet: $PROJECT_DIR/review/all.jpg"
echo "======================================================================"

