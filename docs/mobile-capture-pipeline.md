# Mobile-web capture pipeline + VPS

> **Parent:** [RESEARCH.md §8](../RESEARCH.md#8-custom-dataset-capture--concept-and-components)
> **Position in architecture:** [Layer 2 — pins the long tail and mobile-camera reality](./dataset-architecture.md#layer-2--mobile-web-volunteer-capture)
> **Siblings:** [dataset-architecture](./dataset-architecture.md) · [synthetic-rendering](./synthetic-rendering.md) · [gaussian-splats](./gaussian-splats.md) · [open-questions](./open-questions.md)

## What this layer is actually for

It would be tempting to frame the mobile-web capture app as "the main source of training data." Given what the [synthetic rendering layer](./synthetic-rendering.md) can already do (84–97% of real-data accuracy from CGI alone per the CVPR 2025 HandSynthesis paper), that framing is wrong.

The mobile-web layer's *real* job is **specifically capturing the conditions where synthetic rendering is weakest**:

- Actual phone-camera artifacts: color casts, white-balance shifts, JPEG/HEIC compression, ISO noise, motion blur
- Real demographic and skin-tone variation outside what MANO/NIMBLE source scans cover
- Awkward angles, sleeve occlusion, real-world clutter, off-axis lighting
- The specific Hand_AI use case: someone holding a phone in selfie orientation, hand entering frame at varied distances

This is exactly the failure mode flagged in [RESEARCH.md §4.6](../RESEARCH.md#46-mediapipe--lstm-for-continuous-gesture-and-sign-language-recognition) — the Reddit caveat about MediaPipe landmarks degrading on mobile cameras. **Capturing under exactly those conditions is the entire point.**

The CVPR 2025 finding that "**pose distribution should match the target dataset**" ([details](./synthetic-rendering.md#what-actually-matters-cvpr-2025-ablations)) means even a small number of real captures pays off disproportionately if it shifts the synthetic pipeline's distribution toward what users actually do.

## The mobile-web app side

Conceptually:

1. **Browser opens the camera** (`getUserMedia` / `MediaDevices` API). Mobile-Safari and Chrome both support it; no app store distribution needed.
2. **Show a target gesture prompt** — "make a fist," "point at the camera," etc. Probably with a reference photo or animation.
3. **Capture short bursts** of 5–10 frames per pose, ideally under varied conditions the app nudges the volunteer toward:
   - "Rotate your hand slightly"
   - "Move closer to a window"
   - "Step into shade"
4. **On-device auto-label** with [MediaPipe HandLandmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) via the same `@mediapipe/tasks-vision` package Hand_AI already uses. This yields 21 landmarks per frame at zero server cost.
5. **Confidence-based routing:**
   - High-confidence MediaPipe output → upload frame + landmarks, accept as auto-labeled training data
   - Low-confidence MediaPipe output → **flag for human review** — these are the gold cases, the failures we want to learn from
   - Failed detection → discard or flag separately
6. **Upload** to the VPS over HTTPS. Pre-compress on-device to keep bandwidth modest.

### Why MediaPipe self-labels are good enough

For the high-confidence cases, MediaPipe HandLandmarker is the *exact same model* Hand_AI currently consumes — so its labels match what Hand_AI's downstream classifier will see at inference time. We're not introducing a labeling discrepancy; we're using the existing model as a teacher for a downstream gesture head.

For the low-confidence cases — where MediaPipe is *wrong* about phone images — that's precisely the distribution we need labeled by humans (or by the synthetic pipeline's distribution shift).

## The VPS side

What the server is actually responsible for:

| Function | Why |
|---|---|
| **Ingest + storage** | Receive uploads, store raw frames + landmark JSON. Storage is cheap; moderation is not. |
| **Dedup** | Perceptual hashing (e.g., pHash) to drop near-duplicate uploads. Otherwise one volunteer can pollute the dataset with a thousand near-identical frames. |
| **Quality filtering** | Blur/exposure thresholds. Discard frames below quality floor automatically. |
| **MediaPipe re-validation** | Server-side re-run of HandLandmarker to confirm on-device labels (different model versions, different perf characteristics). |
| **Low-confidence review queue** | Human moderation interface for flagged frames. This is the main human-cost bottleneck. |
| **Demographic/device-class balancing** | Ensure the dataset doesn't over-index on one skin tone, one phone, one geography. |
| **Consent records** | Per-upload consent metadata, retention preferences, withdrawal handling. See [open-questions](./open-questions.md#consent--biometric-data). |
| **Synthetic rendering jobs** | If we self-host the [synthetic pipeline](./synthetic-rendering.md), the VPS GPU runs HandSynthesis-style renders here. Probably the largest single cost. |
| **Splat fitting jobs** | If [Layer 3](./gaussian-splats.md) goes live, MANO + 3DGS fitting per captured orbit. |
| **Label adaptation** | Reconcile skeleton-topology mismatches between sources (MediaPipe vs. MANO vs. NIMBLE conventions). [Why this matters.](./synthetic-rendering.md#what-actually-matters-cvpr-2025-ablations) |
| **Dataset versioning + export** | Snapshotting, train/val/test splits, export format (COCO-style JSON? WebDataset? HuggingFace dataset?). |

### Compute sizing (rough)

A single L4 or 4090-class GPU instance can probably handle a few hundred captures per day plus a continuous trickle of synthetic-rendering jobs. The synthetic rendering at ~1 second per image on an A5000 ([HandSynthesis benchmark](./synthetic-rendering.md#handsynthesis-cvpr-2025--the-most-important-paper-for-this-project)) means a single GPU produces ~80K images per day if it does nothing else. Reasonable for v1.

If [Layer 3](./gaussian-splats.md) is enabled, splat fitting is dramatically more expensive — 30 min to several hours per capture per the Liang et al. benchmarks. Need a dedicated queue, possibly a beefier GPU, and rate-limiting on volunteer submissions.

## Architecture sketch (rough)

```
[mobile browser]
    │ getUserMedia → camera
    │ @mediapipe/tasks-vision → on-device landmarks
    │ confidence routing
    ▼
[HTTPS upload]
    │
    ▼
[VPS API]
    │ dedup (pHash)
    │ quality filter
    │ MediaPipe re-validation
    ├── high-confidence ─→ [dataset store]
    └── low-confidence  ─→ [review queue] ─→ [human moderator] ─→ [dataset store]

[VPS GPU worker pool]
    ├── synthetic rendering (HandSynthesis-style)
    ├── (optional) splat fitting (MANO + 3DGS)
    └── periodic dataset snapshot + export
```

## Open considerations

Deferred to [open-questions](./open-questions.md):

- Authentication and rate-limiting (anonymous vs. logged-in volunteers)
- Consent UX flow — what exactly do volunteers agree to, and how do we let them withdraw later
- Moderation policy — what gets removed (faces in frame, identifiable jewelry, NSFW)
- Whether to use a third-party labeling service for the review queue or build it ourselves
- License and IP terms for the resulting dataset

## Cross-references

- The Hand_AI side that consumes these labels: [warrenrross/Hand_AI](https://github.com/warrenrross/Hand_AI) — specifically the MediaPipe pipeline in [`assets/js/handTracker.js`](https://github.com/warrenrross/Hand_AI/blob/main/assets/js/handTracker.js).
- The synthetic rendering this layer pairs with: [synthetic-rendering](./synthetic-rendering.md).
- The optional splat-capture upgrade: [gaussian-splats](./gaussian-splats.md).
- The model upgrade paths this data feeds into: [RESEARCH.md §7](../RESEARCH.md#7-open-questions--tbd-for-warren).
