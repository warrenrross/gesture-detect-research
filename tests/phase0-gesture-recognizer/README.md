# Phase 0 experiment — reproducible bundle

> **Experiment writeup:** [`docs/experiments/phase0-gesture-recognizer.md`](../../docs/experiments/phase0-gesture-recognizer.md)
> **Roadmap context:** [`docs/roadmap.md` Phase 0](../../docs/roadmap.md#phase-0--decide-whether-to-build-any-of-this-blocking)

This directory contains everything needed to reproduce the Phase 0 experiment that compared Google's pre-trained MediaPipe Gesture Recognizer against Hand_AI v2.2 heuristics on a set of "point" gestures.

## What's in here

```
phase0-gesture-recognizer/
├── README.md                       (this file — agent-readable setup guide)
├── scripts/
│   ├── setup.sh                    (creates venv, installs deps, downloads models)
│   ├── run_experiment.py           (the main runner — Configs 1 + 2)
│   └── probe_handlandmarker.py     (the detection-only probe — Config 3)
├── fixtures/
│   ├── README.md                   (how to provide the test photos)
│   └── EXPECTED_LABELS.csv         (ground truth — all 12 are POINT)
└── prior-results/
    └── phase0_results_2026-05-21.csv  (results from the original run)
```

## Step-by-step reproduction (for an agent or human)

### Prerequisites

- Python 3.10+ (tested on 3.12.8)
- Network access to PyPI and `storage.googleapis.com`
- ~10 GB free disk (mostly for the venv; the models themselves are ~16 MB combined)
- CPU is fine; no GPU required for n=12 inference

### Step 1 — Stage the test photos

The 12 test photos are **not committed to this repo** (size + the screenshots embed Warren's browser session). To reproduce, place the 12 photos in `fixtures/photos/` with their original filenames:

```
fixtures/photos/
├── Screenshot-2026-05-21-at-7.43.42-AM.jpg
├── Screenshot-2026-05-21-at-7.44.02-AM.jpg
├── Screenshot-2026-05-21-at-7.44.32-AM.jpg
├── Screenshot-2026-05-21-at-7.44.50-AM.jpg
├── Screenshot-2026-05-21-at-7.44.58-AM.jpg
├── Screenshot-2026-05-21-at-7.45.43-AM.jpg
├── Screenshot-2026-05-21-at-8.04.41-AM.jpg
├── Screenshot-2026-05-21-at-8.04.59-AM.jpg
├── Screenshot-2026-05-21-at-8.05.24-AM.jpg
├── Screenshot-2026-05-21-at-8.05.38-AM.jpg
├── Screenshot-2026-05-21-at-8.05.49-AM.jpg
└── Screenshot-2026-05-21-at-8.05.58-AM.jpg
```

If filenames differ but ordering matches, also adjust `fixtures/EXPECTED_LABELS.csv` accordingly.

### Step 2 — Run setup

From this directory:

```bash
bash scripts/setup.sh
```

This script:

1. Creates a venv at `./.venv-mp/` (local to this experiment, not your global Python)
2. Installs `mediapipe`, `opencv-python-headless`, `pillow` from PyPI
3. Downloads `gesture_recognizer.task` (~8.4 MB) and `hand_landmarker.task` (~7.8 MB) from Google's CDN into `./models/`
4. Prints the installed versions for the experiment log

Expected runtime: ~2 minutes on a typical machine, dominated by the `pip install` step.

### Step 3 — Run the main experiment

```bash
source .venv-mp/bin/activate
python scripts/run_experiment.py
```

This runs both Config 1 (raw screenshots) and Config 2 (cropped screenshots). Output is printed to stdout and also written to `phase0_results.csv` in this directory.

Expected runtime: ~5–10 seconds total. The MediaPipe pipeline initialization is the slow part; inference is ~50ms per image on CPU.

### Step 4 — Run the detection probe (optional)

```bash
python scripts/probe_handlandmarker.py
```

This runs Config 3 — just HandLandmarker (no gesture head) on both raw and cropped images. Useful to confirm whether detection failures are a property of the gesture pipeline or just upstream detection.

### Step 5 — Compare against prior run

```bash
diff phase0_results.csv prior-results/phase0_results_2026-05-21.csv
```

A clean reproduction should produce identical or near-identical results on the same input photos. If your numbers differ substantially, the most likely causes are:

- Different `mediapipe` version (we ran `0.10.35`)
- Different model file version (Google occasionally updates the `latest` URL — the bundled scripts use `latest`; pin to a specific version if you need bit-for-bit reproduction)
- Cropping numbers differ (the cropping is fixed to `[170:h-85, :]` to match the original run)

## What the original run found

Summarized from [the experiment writeup](../../docs/experiments/phase0-gesture-recognizer.md):

- **0 / 12 frames classified as `Pointing_Up` by the canned Gesture Recognizer.** Hand_AI v2.2 fires `POINT` on all 12 of these same frames.
- **3 / 12 cropped frames had a hand detected** — and on all 3, the canned classifier returned the literal label `"None"` (not `Pointing_Up`), with confidence 0.82–0.88. Same 3 frames are detected by bare HandLandmarker.
- **9 / 12 frames had no hand detected at all.** Partly attributable to the inputs being Hand_AI app screenshots (overlays, sticker occlusion, low contrast) rather than raw webcam frames.

See the writeup for the methodology caveats and the recommended next steps.

## Agent notes — what made this experiment work the first time

If you're a fresh agent picking this up to extend or rerun:

1. **The test photos are Hand_AI app screenshots, not raw hand photos.** This matters because the green skeleton wireframe Hand_AI draws is literally rendered into the pixels you're feeding the canned detector. If you're trying to make a clean comparison, get raw frames instead.
2. **Cropping the browser chrome and HUD bar from the top/bottom matters.** With raw uncropped screenshots, the canned MediaPipe pipeline detected 0 hands. After cropping `[170:h-85, :]` (image height ~1080), 3 of 12 detect cleanly. This is in the runner script already.
3. **`category_name == "None"` is a real outcome, distinct from a no-detection.** Don't conflate them in your scoring. The original run almost missed this distinction.
4. **`Pointing_Up` in the canned vocabulary means index-extended-upward.** Hand_AI's `POINT` accepts any direction. Scoring `Pointing_Up` as a correct `POINT` regardless of orientation is the *most favorable* possible scoring for the canned model — and it still hit 0%.
5. **The MediaPipe `__del__` cleanup throws a `TypeError`** during interpreter shutdown on some platforms. It's noise; ignore it. The actual inference output is fine.
6. **CPU inference is fine for n=12.** Don't bother trying to spin up a GPU for this experiment.

## If extending this experiment

Likely follow-ups, in order of value:

1. **Run on raw webcam frames** (no Hand_AI overlay). The cleanest version of the Phase 0 test. Most likely changes the detection portion of the result but probably not the label-mismatch finding.
2. **Run with [Model Maker](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer)** trained on ~20 examples per Hand_AI gesture. If a tiny custom-trained head succeeds where the canned head fails, the entire HandSynthesis path in Phase 1 may be unnecessary.
3. **Extend to non-point gestures.** This experiment only tested point. Other Hand_AI gestures (fist, open_palm, pinch, near_pinch, thumbs_up) may have different label-mismatch characteristics.
4. **Test the JavaScript / WASM version of MediaPipe Gesture Recognizer.** If you're going to run it in the browser like Hand_AI does, the WASM build may behave subtly differently than the Python build tested here.
