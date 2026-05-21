#!/usr/bin/env python3
"""
Phase 0 — Config 3: bare HandLandmarker detection probe.

Answers the question: when the Gesture Recognizer fails, is it because the
upstream MediaPipe detector can't see the hand, or because the gesture-head
classifier doesn't fire?

Runs HandLandmarker (no gesture head) on both raw and cropped images and
reports detection counts.

See docs/experiments/phase0-gesture-recognizer.md for context.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

EXP_DIR = Path(__file__).resolve().parent.parent
PHOTOS_DIR = EXP_DIR / "fixtures" / "photos"
MODELS_DIR = EXP_DIR / "models"
HAND_MODEL = MODELS_DIR / "hand_landmarker.task"

CROP_TOP = 170
CROP_BOTTOM = 85


def make_landmarker():
    if not HAND_MODEL.exists():
        sys.exit(f"Model missing: {HAND_MODEL}. Run scripts/setup.sh first.")
    base = mp_python.BaseOptions(model_asset_path=str(HAND_MODEL))
    opts = mp_vision.HandLandmarkerOptions(
        base_options=base,
        running_mode=mp_vision.RunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.3,
    )
    return mp_vision.HandLandmarker.create_from_options(opts)


def probe(landmarker, crop: bool) -> tuple[int, int, list[str]]:
    """Returns (detected, total, list_of_detected_filenames)."""
    photos = sorted(PHOTOS_DIR.glob("Screenshot-2026-05-21-at-*.jpg"))
    if not photos:
        sys.exit(f"No photos found in {PHOTOS_DIR}. See fixtures/README.md.")

    detected_files = []
    for path in photos:
        bgr = cv2.imread(str(path))
        if bgr is None:
            continue
        if crop:
            h = bgr.shape[0]
            bgr = bgr[CROP_TOP:h - CROP_BOTTOM, :]
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_image)
        if result.hand_landmarks:
            detected_files.append(path.name)
    return len(detected_files), len(photos), detected_files


def main() -> int:
    landmarker = make_landmarker()

    print("=== HandLandmarker detection probe (no gesture head) ===\n")
    for label, crop in [("raw screenshots", False),
                        ("cropped screenshots", True)]:
        det, total, names = probe(landmarker, crop=crop)
        print(f"  {label}: {det}/{total} hands detected")
        for n in names:
            print(f"    + {n}")
        print()

    print("Compare to Gesture Recognizer results: a match means detection "
          "is the bottleneck;\nmismatch means the gesture head is rejecting "
          "detected hands.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
