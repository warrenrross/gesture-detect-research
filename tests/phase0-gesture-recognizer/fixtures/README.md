# Test fixtures

The 12 test photos used in the original run are **not committed to this repo**:

- They are Hand_AI app screenshots containing Warren's browser session and webcam imagery
- Re-distributing them through git history is unnecessary for the experiment to be reproducible

## To reproduce the original run

Place the 12 photos in `fixtures/photos/` with these exact filenames:

```
Screenshot-2026-05-21-at-7.43.42-AM.jpg
Screenshot-2026-05-21-at-7.44.02-AM.jpg
Screenshot-2026-05-21-at-7.44.32-AM.jpg
Screenshot-2026-05-21-at-7.44.50-AM.jpg
Screenshot-2026-05-21-at-7.44.58-AM.jpg
Screenshot-2026-05-21-at-7.45.43-AM.jpg
Screenshot-2026-05-21-at-8.04.41-AM.jpg
Screenshot-2026-05-21-at-8.04.59-AM.jpg
Screenshot-2026-05-21-at-8.05.24-AM.jpg
Screenshot-2026-05-21-at-8.05.38-AM.jpg
Screenshot-2026-05-21-at-8.05.49-AM.jpg
Screenshot-2026-05-21-at-8.05.58-AM.jpg
```

`EXPECTED_LABELS.csv` ground-truths these files. If your filenames differ, update both that CSV and your photo directory consistently.

## To run with a different photo set

The scripts glob `Screenshot-2026-05-21-at-*.jpg` — adjust that pattern in `scripts/run_experiment.py` and `scripts/probe_handlandmarker.py` if your filenames look different. Also update `EXPECTED_LABELS.csv` to match.

## What the photos contain

Each photo is a screenshot of [Hand_AI](https://warrenrross.github.io/Hand_AI/) running in a browser, captured at the moment the user is making a `POINT` gesture in front of the webcam. All 12 are ground-truth-labeled `POINT` (the v2.1/v2.2 grill rounds discussed the specific failure modes each one represents).

The screenshots include:

- Browser chrome (~170 px at top)
- HUD bar at bottom (~85 px) — shows the model's gesture verdict and HUD metrics
- The webcam feed of the user's hand in the middle
- The Hand_AI app's green skeleton wireframe drawn over the hand (this is rendered into the pixels)
- Sticker emojis placed by previous gestures, scattered across the scene

The `run_experiment.py` script handles cropping the chrome and HUD, but the wireframe overlay and stickers remain in the image — this is exactly what we want for the Phase 0 experiment, because it answers the question "would the canned model work on screenshots Warren has been using to evaluate Hand_AI?" (Answer: no.)

If you want to instead test the canned model on *raw* webcam frames without Hand_AI's overlay, that's a different experiment — see the recommended follow-ups in [`docs/experiments/phase0-gesture-recognizer.md`](../../../docs/experiments/phase0-gesture-recognizer.md#caveats-and-reservations).
