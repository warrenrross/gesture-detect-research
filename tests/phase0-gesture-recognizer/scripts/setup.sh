#!/usr/bin/env bash
# Phase 0 experiment — environment setup.
# Creates a local venv, installs MediaPipe + image deps, downloads the canned
# Gesture Recognizer and Hand Landmarker models.
#
# Run from tests/phase0-gesture-recognizer/  (this script's parent directory).
#
# Idempotent: re-running on an existing venv just re-checks deps/models.

set -euo pipefail

# Resolve directory of this script's parent (the experiment root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$EXP_DIR"

VENV="$EXP_DIR/.venv-mp"
MODELS_DIR="$EXP_DIR/models"

echo "==> Phase 0 experiment setup"
echo "    experiment dir: $EXP_DIR"

# 1. venv
if [[ ! -d "$VENV" ]]; then
    echo "==> Creating venv at $VENV"
    python3 -m venv "$VENV"
else
    echo "==> Reusing existing venv at $VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

# 2. deps
echo "==> Installing dependencies (mediapipe, opencv, pillow)"
pip install --quiet --upgrade pip
pip install --quiet \
    "mediapipe>=0.10.35,<0.11" \
    "opencv-python-headless" \
    "pillow"

# 3. models
mkdir -p "$MODELS_DIR"

GR_URL="https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task"
HL_URL="https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"

if [[ ! -f "$MODELS_DIR/gesture_recognizer.task" ]]; then
    echo "==> Downloading gesture_recognizer.task"
    curl -sSL -o "$MODELS_DIR/gesture_recognizer.task" "$GR_URL"
fi
if [[ ! -f "$MODELS_DIR/hand_landmarker.task" ]]; then
    echo "==> Downloading hand_landmarker.task"
    curl -sSL -o "$MODELS_DIR/hand_landmarker.task" "$HL_URL"
fi

# 4. log versions for the experiment record
echo ""
echo "==> Versions"
python -c "import sys, mediapipe, cv2, PIL; \
print(f'  python:      {sys.version.split()[0]}'); \
print(f'  mediapipe:   {mediapipe.__version__}'); \
print(f'  opencv:      {cv2.__version__}'); \
print(f'  pillow:      {PIL.__version__}')"

echo ""
echo "==> Model sizes"
ls -la "$MODELS_DIR" | tail -n +2

echo ""
echo "==> Setup complete. To run the experiment:"
echo "    source $VENV/bin/activate"
echo "    python scripts/run_experiment.py"
