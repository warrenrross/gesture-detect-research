# Open questions — consent, licensing, scope, sequencing

> **Parent:** [RESEARCH.md §8](../RESEARCH.md#8-custom-dataset-capture--concept-and-components)
> **Siblings:** [dataset-architecture](./dataset-architecture.md) · [synthetic-rendering](./synthetic-rendering.md) · [gaussian-splats](./gaussian-splats.md) · [mobile-capture-pipeline](./mobile-capture-pipeline.md)

Things we don't know yet, organized by category. Each is a roadmap input, not a roadmap blocker.

## Consent / biometric data

Hands are not faces but **may still be biometric data** under some jurisdictions' laws (notably Illinois BIPA, parts of EU GDPR Art. 9 depending on interpretation, and emerging state laws in TX, CA, WA). This affects [the mobile-web capture layer](./mobile-capture-pipeline.md).

Open questions:

- What's the actual legal classification of hand images for a dataset-collection app run by an individual in the US? (Not legal advice — needs a real lawyer if this ships publicly.)
- Do we need explicit, granular consent (per-use case) or is broad "you contribute, we use" sufficient?
- How do we handle volunteer **withdrawal of consent** after a dataset snapshot has been exported and possibly shared?
- Do we need age verification? Minors' biometric data has stricter rules.
- If we ever capture faces incidentally (selfie framing), what's the policy?

Practical implications:

- Cheapest path is **anonymous, no-account capture** with an explicit consent screen each session. Trade-off: no withdrawal mechanism without account.
- Slightly more involved: account-based with per-capture consent metadata and a withdrawal endpoint.
- Either way, **consent strings need to be versioned** so a 2026 snapshot can be tied to whatever the volunteer agreed to in 2026.

## License math

Three different licensing regimes touch this project:

### Upstream model licenses

- **[MANO](https://mano.is.tue.mpg.de)** — research-only by default. Commercial use requires separate Max Planck licensing. Affects [synthetic rendering](./synthetic-rendering.md) and [splat fitting](./gaussian-splats.md).
- **[NIMBLE](https://github.com/reyuwei/NIMBLE_model)** — has its own terms; check before incorporating into a publicly released dataset.
- **[DART / DARTset](https://dart2022.github.io)** — released for research. Re-distribution terms unclear; original textures/accessories may have separate rights.
- **[MediaPipe HandLandmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker)** — Apache 2.0 model, but Google's pre-training data is **proprietary** (see [RESEARCH.md §3](../RESEARCH.md#3-hand_ai-lineage--mediapipe-handlandmarker)). Using its outputs as auto-labels is fine; redistributing its weights or pre-training data is not.
- **[OpenPose hand model](https://github.com/CMU-Perceptual-Computing-Lab/openpose)** — **non-commercial license.** Flagged in [RESEARCH.md §6.2](../RESEARCH.md#62-pretrained-open-weight-models). Don't accidentally pull it into a commercial pipeline.

### Downstream dataset license

If we release the resulting dataset:

- What license? CC-BY? CC-BY-NC? Research-only? Custom?
- Does the license need to inherit any restrictions from upstream models (especially MANO/NIMBLE/DART if they were used in synthesis)?
- Can volunteers reasonably consent to "any future open license" without knowing what that will be?

### Code license

The capture tool itself is separate from the dataset. Probably MIT (matching this research repo) but worth re-confirming if it pulls in copyleft dependencies.

## v1 scope

The dataset-capture concept could be huge. What does v1 actually capture?

Candidates:

- **Hand_AI's current gesture set only:** open palm, point, peace, thumbs up, near-pinch, pinch. Narrow, well-defined, immediately useful, dogfoodable.
- **A broader static gesture vocabulary:** ASL alphabet, numbers, common emoji gestures. More dataset value but more capture burden per volunteer.
- **Motion gestures too:** swipes, waves, pinch-zoom. Different capture flow (video, not bursts), feeds the [§4.6 LSTM upgrade path](../RESEARCH.md#46-mediapipe--lstm-for-continuous-gesture-and-sign-language-recognition).
- **Hand-object interactions:** holding things, pointing at things. Larger dataset value but explodes the variation space.

**Default recommendation:** start with Hand_AI's current set (option 1). Get the full pipeline working end-to-end with the narrowest possible vocabulary, then widen if it works.

## Sequencing — what to build first

Independent of scope, the build order question:

1. **Run the cheap experiment first.** Per [RESEARCH.md §7](../RESEARCH.md#7-open-questions--tbd-for-warren): test [Google's Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer) head-to-head against Hand_AI v2.2 heuristics on the existing 12-photo grill set. If heuristics win or tie, **the entire dataset-capture project may be solving the wrong problem.** Maybe 1–2 hours of work, defers a much larger commitment.
2. **If a learned classifier looks promising:** the [build order from dataset-architecture](./dataset-architecture.md#failure-modes-and-graceful-degradation) is synthetic-first (Layer 1), then mobile capture (Layer 2), then splats (Layer 3 or never). Each layer is independently useful.
3. **The mobile-web app is not a prerequisite for any model improvement.** Layer 1 alone can deliver a working learned classifier. The capture tool is the *quality lever* on top of synthetic data, not the foundation.

## Domain randomization vs. photorealism — where to spend GPU

The [HandSynthesis CVPR 2025 ablations](./synthetic-rendering.md#what-actually-matters-cvpr-2025-ablations) and the [NVIDIA SDR work](https://developer.nvidia.com/blog/structured-domain-randomization-makes-deep-learning-more-accessible/) both point to **diversity > realism**. If true at scale:

- Spending GPU on fancier skin shaders is the wrong axis
- Spending GPU on more aggressive randomization (lighting, backgrounds, occlusion patterns, frequency-domain augmentations) is the right axis
- This affects whether [splat-driven realism (Layer 3)](./gaussian-splats.md) is even the right target to optimize for, vs. just more aggressive randomization in Layer 1

Open question for after Layer 1 is running: **what's the actual marginal accuracy curve as we push realism vs. diversity?** Worth measuring before committing to Layer 3 infra.

## Things we explicitly don't know

- Whether a learned classifier actually beats v2.2 heuristics on Hand_AI's photo set
- Whether HandSynthesis-style synthetic data covers the *gesture-recognition* task as well as it covers the *pose-estimation* task (the paper is benchmarked on pose estimation only)
- Whether HandSplat / GraG code will actually be released and runnable
- Whether the [mobile-camera failure mode from RESEARCH.md §4.6](../RESEARCH.md#46-mediapipe--lstm-for-continuous-gesture-and-sign-language-recognition) is fixable by retraining on phone-camera data, or whether it's a deeper architectural limit of MediaPipe
- What the right gesture vocabulary actually *is* for Hand_AI's downstream use cases
- Whether volunteer recruitment is even feasible at the scale needed (this is partly a marketing/community question, not just a technical one)
