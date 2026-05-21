#!/usr/bin/env python3
"""
Phase 0 experiment — main runner.

Compares Google's pre-trained MediaPipe Gesture Recognizer against Hand_AI v2.2
heuristics on the 12 "POINT" photos from the v2.1/v2.2 grill rounds.

Runs two configurations:
  1. Raw screenshots (1755 x 1080)
  2. Cropped screenshots (browser chrome + HUD bar removed)

Scoring: `Pointing_Up` from the canned model is counted as a correct POINT
(the most favorable possible mapping for the canned model — Hand_AI's POINT
accepts any direction, while Pointing_Up technically means upward only).

Writes phase0_results.csv to the experiment root.

See docs/experiments/phase0-gesture-recognizer.md for the full writeup.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

# Layout: scripts/ is a sibling of fixtures/, models/, and the output CSV.
EXP_DIR = Path(__file__).resolve().parent.parent
PHOTOS_DIR = EXP_DIR / "fixtures" / "photos"
MODELS_DIR = EXP_DIR / "models"
OUT_CSV = EXP_DIR / "phase0_results.csv"
EXPECTED_CSV = EXP_DIR / "fixtures" / "EXPECTED_LABELS.csv"

GESTURE_MODEL = MODELS_DIR / "gesture_recognizer.task"

# Top of frame: 170px of browser chrome; bottom: ~85px of HUD bar.
# Same crop used in the original 2026-05-21 run.
CROP_TOP = 170
CROP_BOTTOM = 85


@dataclass
class Row:
    config: str
    file: str
    expected: str
    gesture: str
    score: float
    hand_present: bool
    correct: bool


def load_expected() -> dict[str, str]:
    """Load expected labels from EXPECTED_LABELS.csv (file -> POINT/etc.)."""
    if not EXPECTED_CSV.exists():
        return {}
    out = {}
    with EXPECTED_CSV.open() as f:
        for r in csv.DictReader(f):
            out[r["file"]] = r["expected"]
    return out


def make_recognizer() -> mp_vision.GestureRecognizer:
    if not GESTURE_MODEL.exists():
        sys.exit(f"Model missing: {GESTURE_MODEL}. Run scripts/setup.sh first.")
    base = mp_python.BaseOptions(model_asset_path=str(GESTURE_MODEL))
    opts = mp_vision.GestureRecognizerOptions(
        base_options=base,
        running_mode=mp_vision.RunningMode.IMAGE,
        num_hands=1,
        min_hand_detection_confidence=0.3,  # permissive: surface marginal detections
    )
    return mp_vision.GestureRecognizer.create_from_options(opts)


def run_one(recognizer, img_bgr) -> tuple[str, float, bool]:
    """Returns (label, score, hand_present)."""
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = recognizer.recognize(mp_image)

    if result.gestures and result.gestures[0]:
        top = result.gestures[0][0]
        # Note: top.category_name can be literally "None" — meaning detected-hand-
        # but-no-gesture-match. That's distinct from no detection.
        return top.category_name, float(top.score), True

    return "NONE", 0.0, bool(result.hand_landmarks)


def process_config(recognizer, config_name: str, expected: dict[str, str],
                   crop: bool) -> list[Row]:
    rows: list[Row] = []
    photos = sorted(PHOTOS_DIR.glob("Screenshot-2026-05-21-at-*.jpg"))
    if not photos:
        sys.exit(f"No photos found in {PHOTOS_DIR}. See fixtures/README.md.")

    for path in photos:
        bgr = cv2.imread(str(path))
        if bgr is None:
            rows.append(Row(config_name, path.name, expected.get(path.name, "?"),
                            "READ_ERR", 0.0, False, False))
            continue

        if crop:
            h = bgr.shape[0]
            bgr = bgr[CROP_TOP:h - CROP_BOTTOM, :]

        label, score, hand = run_one(recognizer, bgr)
        is_correct = (label == "Pointing_Up")
        rows.append(Row(config_name, path.name,
                        expected.get(path.name, "POINT"),
                        label, round(score, 3), hand, is_correct))

    return rows


def print_table(rows: list[Row], config_name: str) -> None:
    name_w = max(len(r.file) for r in rows)
    print(f"\n=== Config: {config_name} ===")
    print(f"{'file':<{name_w}}  {'expected':<8}  {'gesture':<14}  "
          f"{'score':>6}  {'hand':>5}  result")
    print("-" * (name_w + 50))
    correct = 0
    for r in rows:
        mark = "POINT" if r.correct else "MISS "
        print(f"{r.file:<{name_w}}  {r.expected:<8}  {r.gesture:<14}  "
              f"{r.score:>6.3f}  {str(r.hand_present):>5}  {mark}")
        correct += int(r.correct)
    print("-" * (name_w + 50))
    n = len(rows)
    pct = (correct / n * 100) if n else 0.0
    print(f"  Pointing_Up matches: {correct}/{n} = {pct:.0f}%")
    hands = sum(int(r.hand_present) for r in rows)
    print(f"  Hands detected:      {hands}/{n}")


def main() -> int:
    expected = load_expected()
    recognizer = make_recognizer()

    all_rows: list[Row] = []
    all_rows += process_config(recognizer, "raw",     expected, crop=False)
    print_table([r for r in all_rows if r.config == "raw"], "raw screenshots")

    all_rows += process_config(recognizer, "cropped", expected, crop=True)
    print_table([r for r in all_rows if r.config == "cropped"],
                "cropped screenshots (browser chrome + HUD removed)")

    # CSV output
    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(all_rows[0]).keys()))
        writer.writeheader()
        for r in all_rows:
            writer.writerow(asdict(r))

    print(f"\n==> Wrote {OUT_CSV}")
    print(f"    Compare against prior-results/phase0_results_2026-05-21.csv "
          f"for regression check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
