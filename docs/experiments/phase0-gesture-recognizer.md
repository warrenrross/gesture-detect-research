# Experiment: Phase 0 — MediaPipe Gesture Recognizer vs. Hand_AI v2.2

> **Date:** 2026-05-21
> **Operator:** Computer (sandbox) + Warren (photos)
> **Parent:** [`docs/roadmap.md` — Phase 0](../roadmap.md#phase-0--decide-whether-to-build-any-of-this-blocking)
> **Reproducible bundle:** [`tests/phase0-gesture-recognizer/`](../../tests/phase0-gesture-recognizer/)
> **Status:** Inconclusive due to methodology caveats. Recommend proceeding to Phase 1 cautiously, with a follow-up cleaner experiment as #2 below.

## Goal

Test [Google's MediaPipe Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer) (the canned, pre-trained model) head-to-head against Hand_AI v2.2's heuristic classifier on the 12 photos from the v2.1/v2.2 grill rounds. Decide whether building a custom dataset is justified, or whether the canned upstream pipeline already does the job.

This is the blocking gate from [Phase 0 of the roadmap](../roadmap.md#phase-0--decide-whether-to-build-any-of-this-blocking) — without it, every other phase risks solving a problem that doesn't exist.

## Test set

12 photos, all from May 21 2026 sessions, all confirmed as `POINT` gestures in the v2.1 grill (turn 36) and v2.2 grill (turn 39) of Hand_AI development. Filenames preserved:

| # | File | Pose description (from prior grill rounds) | v2.2 verdict |
|---|---|---|---|
| 1 | `7.43.42-AM` | Side view, finger pointing left, palm up | POINT ✓ |
| 2 | `7.44.02-AM` | Same hand, fingers slightly more curled | POINT ✓ |
| 3 | `7.44.32-AM` | Hand close to camera, side-on point, thumb extended | POINT ✓ |
| 4 | `7.44.50-AM` | Palm-up point | POINT ✓ |
| 5 | `7.44.58-AM` | Palm-down point, fingers curled tightly under | POINT ✓ |
| 6 | `7.45.43-AM` | Palm-down point, fingers tucked into palm | POINT ✓ |
| 7 | `8.04.41-AM` | Side point, thumb out under index | POINT ✓ |
| 8 | `8.04.59-AM` | Side point, thumb tucked | POINT ✓ |
| 9 | `8.05.24-AM` | Palm-down point, thumb extended out | POINT ✓ |
| 10 | `8.05.38-AM` | Palm-down point (red tip ✓ in HUD) | POINT ✓ |
| 11 | `8.05.49-AM` | Palm-down point, thumb out | POINT ✓ |
| 12 | `8.05.58-AM` | Palm-down point (red tip ✓ in HUD) | POINT ✓ |

**Ground truth:** all 12 are `POINT` per Hand_AI's vocabulary. Hand_AI v2.2 fires `POINT` on all 12. The expected `Pointing_Up` rate from the canned Gesture Recognizer is the question this experiment answers.

## Methodology

### Environment

- Python 3.12.8 in a fresh `venv`
- `mediapipe==0.10.35`, `opencv-python-headless`, `pillow`
- Pre-trained `gesture_recognizer.task` (float16, 8.4 MB) from Google's CDN
- Pre-trained `hand_landmarker.task` (float16, 7.8 MB) for the secondary detection check
- CPU-only inference (no GPU in sandbox)
- Linux sandbox, no special hardware

Exact reproduction recipe lives in [`tests/phase0-gesture-recognizer/README.md`](../../tests/phase0-gesture-recognizer/README.md). Designed to run in any clean Python 3.12 environment in roughly two minutes.

### Scoring rubric

Gesture Recognizer outputs one of: `None`, `Closed_Fist`, `Open_Palm`, `Pointing_Up`, `Thumb_Down`, `Thumb_Up`, `Victory`, `ILoveYou`.

Mapping to Hand_AI vocabulary:

- `Pointing_Up` → scored as a correct `POINT`
- Any other label (or no detection) → incorrect

**Caveat:** Gesture Recognizer's `Pointing_Up` label semantically means "index extended upward". Hand_AI's `POINT` accepts any direction. Scoring `Pointing_Up` as `POINT` regardless of direction is the *most favorable* possible reading for the canned model — anything stricter would be even worse.

### Runs performed

Three configurations to isolate detection vs. classification failure modes:

1. **Raw screenshots** (1755 × 1080) → Gesture Recognizer with default thresholds
2. **Cropped screenshots** (1755 × 825, browser chrome + HUD bar removed) → Gesture Recognizer with `min_hand_detection_confidence=0.3`
3. **HandLandmarker (no gesture head)** on raw and cropped → answers: does the upstream MediaPipe detection even *see* the hand on these images?

## Results

### Configuration 1 — raw screenshots, Gesture Recognizer

| # | File | Top label | Confidence | Hand seen | Correct? |
|---|---|---|---|---|---|
| 1–12 | all | `NONE` | 0.000 | False | MISS |

**0 / 12 (0%).** Zero hands detected on any frame.

### Configuration 2 — cropped screenshots, Gesture Recognizer

| # | File | Top label | Confidence | Hand seen | Correct? |
|---|---|---|---|---|---|
| 1 | 7.43.42-AM | NONE | 0.000 | False | MISS |
| 2 | 7.44.02-AM | NONE | 0.000 | False | MISS |
| 3 | 7.44.32-AM | NONE | 0.000 | False | MISS |
| 4 | 7.44.50-AM | NONE | 0.000 | False | MISS |
| 5 | 7.44.58-AM | NONE | 0.000 | False | MISS |
| 6 | 7.45.43-AM | NONE | 0.000 | False | MISS |
| 7 | 8.04.41-AM | **`None`** (literal label) | 0.816 | **True** | MISS |
| 8 | 8.04.59-AM | **`None`** (literal label) | 0.881 | **True** | MISS |
| 9 | 8.05.24-AM | **`None`** (literal label) | 0.876 | **True** | MISS |
| 10 | 8.05.38-AM | NONE | 0.000 | False | MISS |
| 11 | 8.05.49-AM | NONE | 0.000 | False | MISS |
| 12 | 8.05.58-AM | NONE | 0.000 | False | MISS |

**0 / 12 (0%) `Pointing_Up`.** But — **3 / 12 hands were detected** on cropped images. On all 3, the Gesture Recognizer's classifier head returned the literal label `"None"` with confidence 0.82–0.88, meaning "I see a hand, but the pose doesn't match any of my 7 canned gestures."

### Configuration 3 — HandLandmarker detection probe

| Input | Hands detected |
|---|---|
| Raw screenshots | 0 / 12 |
| Cropped screenshots | 3 / 12 |

The detection numbers match exactly between HandLandmarker and the Gesture Recognizer's internal detection step. The same three photos are detected by both, the rest by neither.

## What the result actually means

Two independent findings, with very different confidence levels:

### Finding 1 — Label-vocabulary mismatch *(strong, methodology-independent)*

**On the 3 frames where the canned model successfully detected a hand, it returned `None`, not `Pointing_Up`.** Confidence 0.82–0.88. The canned model's `Pointing_Up` label is biased toward an upward-oriented index finger; the three detected frames are all side-on points (8:04:41, 8:04:59, 8:05:24), which the model declines to classify as `Pointing_Up`.

This is a clean finding. It means **even with perfect detection, the canned model's label vocabulary does not cover Hand_AI's "point in any direction" semantics.** The canned model can't be a drop-in replacement for Hand_AI v2.2's point detector without retraining.

### Finding 2 — Detection failure *(suggestive, methodology-caveated)*

9 of 12 frames had no hand detected at all. But these test images are *not raw webcam frames* — they are screenshots of the Hand_AI app, which means:

- The hand region is letterboxed inside browser chrome
- The hand has a **green skeleton wireframe drawn on top of it** by Hand_AI's existing visualization layer
- Sticker emojis partially occlude parts of the scene (some directly over the hand region)
- Low ambient light + Hand_AI's dark overlay

This is not the input distribution the canned model was trained for. Some or all of the detection failures may disappear on raw webcam frames.

**This finding is suggestive but inconclusive.** A clean follow-up requires raw webcam frames from the same poses.

## Comparison summary

| Metric | Gesture Recognizer (canned) | Hand_AI v2.2 |
|---|---|---|
| Correctly fires `POINT` | **0 / 12** | **12 / 12** |
| Hand detected | 3 / 12 (cropped); 0 / 12 (raw) | 12 / 12 |
| Label fits Hand_AI vocabulary | No (`Pointing_Up` ≠ point-any-direction) | Yes (native) |

Hand_AI v2.2 wins this test set 12-0.

## Decision

Phase 0's framing was binary: *heuristics win or tie → reconsider; canned model wins → proceed differently.* The result is unambiguous on this test set: **Hand_AI v2.2 wins 12-0.**

**But two important caveats temper this conclusion:**

1. The test set is biased toward Hand_AI's recent failure modes (the v2.1/v2.2 grill set was *selected* because these poses broke prior heuristic versions). It is *not* a representative sample of all the gestures the system needs to handle.
2. The detection-failure portion of the result is partly an artifact of using app-screenshot data rather than raw webcam frames.

### Recommended next step

Proceed to **Phase 1** of the roadmap (synthetic baseline training), but with two additional checkpoints:

1. **Rerun this experiment with raw webcam frames** before committing significant Phase 1 work. If the canned model suddenly hits 80%+ on clean inputs, the calculus changes substantially.
2. **Try MediaPipe Model Maker** ([docs](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer)) before standing up the full HandSynthesis pipeline. Model Maker fine-tunes the gesture head on a small custom dataset (sometimes dozens of examples), which is *much* less infrastructure than synthetic rendering. If Model Maker on raw frames hits the bar, the entire HandSynthesis path may be unnecessary.

The roadmap's Phase 1 plan is still the most thorough fallback if neither of those works, but they are cheaper experiments worth running first.

## Caveats and reservations

In the spirit of not pretending more rigor than this experiment had:

- **Test set is intentionally adversarial.** All 12 frames are Hand_AI's known failure modes from prior versions. The canned model never had a chance to score well on a "clean" subset of poses because there is no such subset in this test set.
- **Test inputs are not the canned model's native distribution.** Hand_AI screenshots have overlays, low contrast, and small hand regions that depress detection.
- **`Pointing_Up` was scored generously** as a correct `POINT` regardless of orientation. The canned model still managed 0% under this most-favorable mapping.
- **n = 12** is too small for any quantitative claim. The qualitative finding (label mismatch) is robust; specific percentages are not.
- **One model version tested.** Future Gesture Recognizer releases or custom-trained variants may behave differently.

## Reproducibility

Full reproduction bundle: [`tests/phase0-gesture-recognizer/`](../../tests/phase0-gesture-recognizer/). The bundle includes the script, model-download command, README walkthrough, and the prior-run output CSV for comparison.

Test fixtures (the 12 photos) are **not committed** to the repo for size + privacy reasons. To reproduce, point the script at a directory of the same 12 photos. See the bundle README for details.

## Cross-references

- Roadmap: [`docs/roadmap.md` Phase 0](../roadmap.md#phase-0--decide-whether-to-build-any-of-this-blocking) — the gate this experiment was designed to answer
- Next phase if proceeding: [`docs/roadmap.md` Phase 1](../roadmap.md#phase-1--synthetic-baseline-that-beats-v22-heuristics) — synthetic baseline via HandSynthesis
- Cheaper alternative to Phase 1: [Google's Model Maker](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer) — listed in the recommendations above
- The prior grill rounds that produced the test set: Hand_AI [PR #5](https://github.com/warrenrross/Hand_AI/pull/5) (v2.1) and Hand_AI [PR #6](https://github.com/warrenrross/Hand_AI/pull/6) (v2.2). v2.2 thresholds: `POINT_DOMINANCE = 1.6`, thumb-tuck tiebreaker for near_pinch.
