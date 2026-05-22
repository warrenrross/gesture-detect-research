# Classification vs. localization in the Hand_AI pipeline

> **Parent:** [`RESEARCH.md` §8](../RESEARCH.md#8-custom-dataset-capture--concept-and-components)
> **Related:** [`docs/roadmap.md`](./roadmap.md) · [`docs/experiments/phase0-gesture-recognizer.md`](./experiments/phase0-gesture-recognizer.md) · [`docs/synthetic-rendering.md`](./synthetic-rendering.md)

This doc exists because the question keeps coming up in different forms: *"if we retrain the classifier, can it tell us where to grab the emoji?"* The answer is no, and the reason is that Hand_AI's pipeline already separates *what gesture is happening* from *where on the screen it's happening*. Anything we change in the classifier head only affects the first question.

## The two questions, per frame

Every frame Hand_AI processes is two independent answers:

1. **What gesture?** — a label like `point`, `pinch`, `fist`, `open_palm`. A *classifier* answers this.
2. **Where on screen?** — `(x, y)` coordinates of the relevant anchor point (fingertip for point, midpoint of thumb + index for pinch, palm centroid for fist). A *landmark detector* answers this.

These are produced by two different parts of the MediaPipe pipeline and they don't share parameters.

```
                  ┌──────────────────────┐
   webcam frame ──▶│  Hand detector       │── bbox of hand
                  └──────────┬───────────┘
                             ▼
                  ┌──────────────────────┐
                  │  HandLandmarker      │── 21 landmarks with (x,y,z)
                  └──────┬───────────────┘     ─────── THIS is "where"
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
   ┌────────────────┐     ┌─────────────────────┐
   │ Classifier     │     │ Hand_AI app logic   │
   │ head (gesture) │     │ — maps fingertip    │
   │ ─── "what" ────│     │   to screen targets │
   └────────────────┘     └─────────────────────┘
```

## What each candidate classifier changes

| Classifier | What it changes | What stays the same |
|---|---|---|
| **Hand_AI v2.2 heuristics** (today) | Hand-tuned math on the 21 landmarks. | Landmarks (and therefore targeting) come from MediaPipe HandLandmarker. |
| **Canned MediaPipe Gesture Recognizer** | A pretrained classifier head Google ships, with the 8-label vocab (`None, Closed_Fist, Open_Palm, Pointing_Up, Thumb_Down, Thumb_Up, Victory, ILoveYou`). | Same HandLandmarker upstream, same landmarks, same targeting. |
| **Model Maker retrained head** | The same head architecture trained on *your* labels. You can define `point_any_direction` to fix the vocab mismatch from [Phase 0](./experiments/phase0-gesture-recognizer.md). | Same HandLandmarker upstream, same landmarks, same targeting. |
| **Phase 1 synthetic-trained MLP** | A head trained on landmarks extracted from synthetic renders. | Same HandLandmarker upstream, same landmarks, same targeting. |

In every row, the landmarks are coming from the same place and the targeting math sits in Hand_AI's app code, not in the model. **Swapping the classifier doesn't add or remove any spatial capability.**

## Anchor points Hand_AI already uses

The [MediaPipe HandLandmarker model card](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) defines 21 landmarks per hand in normalized `(x, y, z)` image coordinates. The ones that matter for current Hand_AI gestures:

| Gesture | Anchor | Landmark index(es) |
|---|---|---|
| Point | Index fingertip | 8 |
| Pinch / near-pinch | Midpoint of thumb tip + index tip | 4 and 8 |
| Fist / grab | Palm centroid | Mean of 0, 5, 9, 13, 17 |
| Open palm | Palm centroid | Same as fist |
| Thumbs up | Thumb tip | 4 |

These coordinates are already what Hand_AI consumes for emoji hit-testing today. Whichever classifier wins, the app keeps consuming them.

## Two failure modes — and which one each layer fixes

This is the practical version of the distinction:

| Failure mode | Symptom | Layer that fixes it |
|---|---|---|
| **Hand not found** | No landmarks, no gesture, no target. The 9/12 result on Phase 0 cropped photos. | The *detector + landmarker*, i.e. HandLandmarker itself. This is what [synthetic data augmentation](./synthetic-rendering.md) is supposed to help with — robustness of the landmarker to mobile-camera artifacts, lighting, etc. |
| **Hand found, wrong/missing label** | Landmarks present, fingertip coordinates fine, but the classifier says `None` or the wrong gesture. The 3/12 cropped-photo case where the canned model returned `"None"` on real points. | The *classifier head*. This is the only thing Model Maker (or a Phase 1 synthetic-trained head) actually moves. |

Model Maker only fixes the second failure mode. If the hand isn't detected upstream, neither targeting nor classification has anything to work with — that's a [Phase 1](./roadmap.md#phase-1--synthetic-baseline-that-beats-v22-heuristics) problem (or a "use raw webcam frames instead of HUD-overlaid screenshots" problem).

## So: does retraining the classifier help with targeting?

No. The targeting signal is the fingertip/centroid coordinate from HandLandmarker, which is produced before the classifier even runs and is identical across every roadmap option.

**What retraining the classifier *does* help with** is making sure that when Hand_AI says "this is a point, fire the destroy emoji at the fingertip," the "this is a point" half is correct on the actual gesture vocabulary the game uses — including side-on points and palm-down points that the canned `Pointing_Up` label rejects.

That's the question Model Maker answers cheaply, and it's the only one a different classifier head can answer.

## Pointers

- [`docs/experiments/phase0-gesture-recognizer.md`](./experiments/phase0-gesture-recognizer.md) — the original 0/12 result that motivated this distinction.
- [`docs/roadmap.md`](./roadmap.md) — Phase 0 (gate), Phase 1 (synthetic-trained head), Phase 2 (ship), Phase 3 (per-player splat capture).
- [`docs/synthetic-rendering.md`](./synthetic-rendering.md) — what synthetic data is actually for (landmark robustness + classifier training).
- [MediaPipe HandLandmarker model card](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) — landmark index reference.
- [MediaPipe Model Maker for Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer) — what the retraining call actually does.
