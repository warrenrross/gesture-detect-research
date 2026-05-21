# Dataset architecture — three layers, side by side

> **Parent:** [RESEARCH.md §8](../RESEARCH.md#8-custom-dataset-capture--concept-and-components)
> **Siblings:** [synthetic-rendering](./synthetic-rendering.md) · [gaussian-splats](./gaussian-splats.md) · [mobile-capture-pipeline](./mobile-capture-pipeline.md) · [open-questions](./open-questions.md)

The mental model: **three data sources, each strongest where the others are weakest**. They are not competing options — they're cooperating layers that each fill a specific gap. Each layer also fails gracefully: drop any one and the others still produce a working pipeline.

## The framing

| Axis | Synthetic CGI ([details](./synthetic-rendering.md)) | Mobile capture ([details](./mobile-capture-pipeline.md)) | Static splats ([details](./gaussian-splats.md)) |
|---|---|---|---|
| **Labels** | Perfect, free, infinite | MediaPipe auto-labels (inherit MP errors) | MANO fit during reconstruction → perfect 3D joints |
| **Lighting/background/pose variation** | Trivial — just randomize | Limited to what volunteers give you | Re-render any background once captured |
| **Skin realism, age, hair, scars, jewelry** | OK but uncanny; [DART](https://dart2022.github.io) ships 325 textures | Real and free | Real, captured per individual |
| **Long-tail / rare cases** | Easy to script (if you have the rigs) | Hard — requires recruiting | Captures whoever volunteers |
| **Mobile camera artifacts** | Must add synthetically (compression, ISO noise, color cast) | Native — the whole point | Inherits whatever you shot with |
| **Cost** | Compute only — ~1 sec/image on a single GPU | Volunteer time + VPS + moderation | Volunteer time + ~30 min cloud processing per scan |
| **Consent / biometric concerns** | None | Real, jurisdiction-dependent — see [open-questions](./open-questions.md) | Real |
| **Sim-to-real gap** | The whole challenge | None | Minor (rendering artifacts) |

The headline: **synthetic provides volume, mobile capture pins the long tail and mobile-camera reality, splats are a force multiplier that turns one volunteer-minute into thousands of labeled views.**

## v1 architecture (proposed)

A coherent pipeline that uses all three layers cooperatively:

### Layer 1 — Synthetic baseline (Day 1, no users needed)

Stand up the [HandSynthesis](https://github.com/delaprada/HandSynthesis) pipeline locally and generate ~100–500K images covering the target gestures using its recommended settings:

- HDRI indoor/outdoor backgrounds (~300 scenes is sufficient — performance plateaus there per the CVPR 2025 ablations, [details](./synthetic-rendering.md#what-actually-matters-cvpr-2025-ablations))
- [NIMBLE](https://github.com/reyuwei/NIMBLE_model) hand textures
- Forearm included (not floating hands)
- Amplitude spectrum augmentation during training
- Object occlusions composited in

Train the initial model entirely on this. Expected accuracy: **84–97% of real-data parity** per the [HandSynthesis CVPR 2025 paper](https://arxiv.org/html/2503.19307v1), before a single volunteer touches the app.

This de-risks the project. Even if the web app never ships or sees zero traffic, there's a working model.

### Layer 2 — Mobile-web volunteer capture

The web app's *real* purpose isn't generic hand images — it's specifically capturing the conditions where the synthetic pipeline is weakest:

- Actual phone-camera color casts and white balance
- JPEG/HEIC compression artifacts
- Low-light noise and motion blur
- Awkward selfie angles, occlusion by sleeves, real-world clutter
- Demographic and skin-tone variation that DART's 325 textures don't cover

Auto-label with [MediaPipe HandLandmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) for the easy frames; **flag low-confidence frames for human review — those are the gold.** They're precisely the cases the model needs to learn from. See [mobile-capture-pipeline](./mobile-capture-pipeline.md) for the full architecture.

The CVPR 2025 ablation that "pose distribution should match the target" ([details](./synthetic-rendering.md#what-actually-matters-cvpr-2025-ablations)) means **even a small number of real captures pays off disproportionately** if it shifts the synthetic pose distribution toward what your users actually do.

### Layer 3 — Static splats as the "personal long-tail" layer

Optional v2. Volunteers who want to contribute more do a 30-second phone-video orbit of one held gesture. Server fits MANO + a static splat, then renders thousands of synthetic views of *that specific individual's hand* in arbitrary lighting and backgrounds.

This is the only path that gets real skin realism for underrepresented demographics without recruiting them in massive numbers. The splat is essentially a per-volunteer "skin" you can pipe into the synthetic renderer. See [gaussian-splats](./gaussian-splats.md) for capture mechanics and feasibility.

Caveat: only **held poses** are scannable today — articulating-hand splatting is still research-grade. So this layer multiplies *pose-and-individual coverage*, not motion coverage.

### What the VPS actually does

Layer-by-layer:

- **Layer 1:** runs the rendering jobs (synthetic generation is the main GPU justification)
- **Layer 2:** receives uploads, dedupes (perceptual hash), filters quality (blur/exposure), runs MediaPipe auto-labeling, queues low-confidence frames for review, balances demographics/device-class in dataset assembly
- **Layer 3:** runs the splat fitting (MANO + 3DGS) and the re-rendering jobs
- **Cross-cutting:** label adaptation for skeleton topology mismatches between sources ([why this matters](./synthetic-rendering.md#what-actually-matters-cvpr-2025-ablations)), versioning, consent records, dataset export

## Failure modes and graceful degradation

| If this layer fails | What remains |
|---|---|
| Layer 3 (splats) | Layers 1+2 still produce a competitive dataset. This layer is purely additive. |
| Layer 2 (mobile capture) | Layer 1 alone reaches **84–97%** of real-data accuracy per HandSynthesis. Ship the synthetic-only model. |
| Layer 1 (synthetic) | Back to a labeling problem we don't want. **Layer 1 is the load-bearing one.** |

That ordering is also the **build order**: synthetic first, mobile capture second, splats third (or never).

## Where the heuristic question goes

Independent of any of this, there's the prior question from [RESEARCH.md §7](../RESEARCH.md#7-open-questions--tbd-for-warren): is a learned classifier even better than the current Hand_AI v2.2 heuristics? That experiment is cheap — try [Google's Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer) head-to-head on the same 12 photos used in the v2.1/v2.2 grill rounds. If heuristics win or tie, the entire dataset-capture project might be solving the wrong problem. **Run that experiment before committing to the architecture above.**

## Open issues feeding the roadmap

Tracked separately in [open-questions](./open-questions.md):

- Biometric / consent / IRB-ish concerns for Layer 2
- MANO and NIMBLE license restrictions (research-only by default) for Layers 1 and 3
- v1 gesture vocabulary scope — do we capture just Hand_AI's current set, or aim broader?
- Domain randomization vs. photorealism — where to spend GPU
