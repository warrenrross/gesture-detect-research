# Roadmap — synthetic-first dataset + personal hyperpersonalization

> **Status:** Starting point, not finalized. Drafted May 2026 from Warren's framing: synthetic-first custom dataset for Hand_AI, plus a per-player capture tool for personal hyperpersonalization.
>
> **Parent:** [RESEARCH.md §8](../RESEARCH.md#8-custom-dataset-capture--concept-and-components)
> **Siblings:** [dataset-architecture](./dataset-architecture.md) · [synthetic-rendering](./synthetic-rendering.md) · [gaussian-splats](./gaussian-splats.md) · [mobile-capture-pipeline](./mobile-capture-pipeline.md) · [open-questions](./open-questions.md)

## The shape of the plan

Two distinct deliverables, sequenced:

1. **A custom synthetic dataset + trained model** that beats Hand_AI v2.2's heuristics on its current gesture vocabulary. This is the load-bearing piece — it ships an improved Hand_AI without requiring any volunteer to do anything.
2. **A per-player 3D-capture tool** that lets Hand_AI players contribute a low-grade 3D representation of *their own* hand in the game's key poses, which feeds a personalized fine-tuning step on top of the baseline model.

The second is downstream of the first. The first has to actually work and ship before the second is worth building. Both are *long arcs*, not single sprints.

This doc is the **starting point** for that roadmap, structured so each phase has a clear go/no-go decision before the next phase starts.

## Why this ordering

- The [synthetic pipeline](./synthetic-rendering.md) provides ~85–97% of real-data accuracy on its own (per the [CVPR 2025 HandSynthesis paper](https://arxiv.org/html/2503.19307v1)) before any user lifts a finger. **That is the value-creating layer.** Ship that, players get a better Hand_AI immediately.
- The [splat-based personal capture](./gaussian-splats.md) is the *force multiplier on the long tail* — it covers individuals whose hands fall outside the synthetic distribution. But it's only worth offering players if the baseline they're personalizing is itself good.
- Going the other direction (capture tool first, then training) means asking players to invest time before the system has anything to give them. Worse engagement, worse data quality, worse signal on whether the project is working.

## Phase 0 — Decide whether to build any of this *(blocking)*

Before committing to anything in Phase 1+, run the cheap experiment from [RESEARCH.md §7](../RESEARCH.md#7-open-questions--tbd-for-warren):

- **Goal:** Test [Google's MediaPipe Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer) head-to-head against Hand_AI v2.2 heuristics on the same 12 photos from the v2.1/v2.2 grill rounds.
- **Effort:** ~1–2 hours. Drop the canned model into a sandbox, run it on the 12 photos, score per-gesture accuracy against the v2.2 results in [AGENT_NOTES.md](https://github.com/warrenrross/Hand_AI/blob/main/AGENT_NOTES.md).
- **Decision rule:**
  - **Heuristics win or tie clearly →** the dataset-capture project may be solving the wrong problem. Reconsider scope before proceeding.
  - **Canned model wins clearly →** confirms a learned classifier is the right direction. Continue, but also try Gesture Recognizer + [Model Maker](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer) on a tiny custom-class set before going synthetic — Model Maker may already cover the need with far less infrastructure.
  - **Mixed result →** most likely outcome. Continue to Phase 1, but ablate against the canned model as a baseline throughout.

This phase is non-negotiable. Skipping it risks building an entire pipeline that loses to a 10-line MediaPipe call.

### Phase 0 — first run (May 21, 2026)

First pass executed. **Full writeup:** [`docs/experiments/phase0-gesture-recognizer.md`](./experiments/phase0-gesture-recognizer.md). **Reproducible bundle:** [`tests/phase0-gesture-recognizer/`](../tests/phase0-gesture-recognizer/).

Headline numbers on the 12 v2.2 grill-round photos, all ground-truth POINT:

- Canned Gesture Recognizer, raw screenshots: **0/12** `Pointing_Up` matches, **0/12** hands detected at all.
- Canned Gesture Recognizer, browser-chrome cropped: **0/12** `Pointing_Up` matches, **3/12** hands detected — and on those 3, the model returned literal label `"None"` with 0.82–0.88 confidence ("hand seen, no gesture matched").
- Hand_AI v2.2 heuristics: fires POINT on all 12 (ground truth).

**Caveat:** these were screenshots with HUD overlays, stickers, and low contrast — not raw webcam frames. The detection failures are mostly an input-quality artifact, not a fair model evaluation. What is *not* a caveat is the **label-vocabulary mismatch**: even on the 3 photos where the model found the hand, side-on and palm-down points returned `"None"`. `Pointing_Up` is not the same class as Hand_AI's "point in any direction."

**Decision:** Mixed result — proceed to Phase 1 cautiously. Two cheap follow-ups before committing to full synthetic infrastructure:

1. Rerun on raw webcam frames (not screenshots) to separate detection failure from classification failure.
2. Try Gesture Recognizer + [Model Maker](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer) on a tiny custom `point_any_direction` class — if Model Maker closes the gap with ~50–200 photos, the full synthetic pipeline may be overkill for what's left of Hand_AI's vocabulary.

Neither follow-up has run yet.

## Phase 1 — Synthetic baseline that beats v2.2 heuristics

**Goal:** A trained gesture classifier that beats Hand_AI v2.2 on its own grill-round photos, trained entirely on synthetic data. No volunteers, no mobile-web app, no splats.

### Phase 1a — First synthetic spike

- Clone [HandSynthesis](https://github.com/delaprada/HandSynthesis) and get its rendering pipeline running locally.
- Render a small batch (~10K images) targeting Hand_AI's current gesture vocabulary: `fist`, `pinch`, `near_pinch`, `point`, `open_palm`, `thumbs_up`.
- Author MANO pose parameters for each gesture, with deliberate variation in finger curl, rotation, palm orientation, and forearm position. The CVPR 2025 ablations say pose distribution should match the target real distribution — for Hand_AI that means roughly forward-facing selfie geometry, not the grasp-heavy poses HandSynthesis defaults to.
- Use HandSynthesis's recommended settings: ~300 HDRI scenes, NIMBLE textures, forearm included, amplitude spectrum augmentation, object occlusions composited in. ([Details](./synthetic-rendering.md#what-actually-matters-cvpr-2025-ablations).)

### Phase 1b — Train a tiny head

- Run [MediaPipe HandLandmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) over each synthetic image to extract 21 landmarks (matching exactly what Hand_AI consumes at inference).
- Train a [kinivi/Kazuhito00-style](https://github.com/kinivi/hand-gesture-recognition-mediapipe) MLP head on the resulting landmark CSVs.
- Optionally also train a raw-pixel classifier (small CNN, MobileNet-class) to compare against the landmark-only approach. The [§4.6 Reddit caveat](../RESEARCH.md#46-mediapipe--lstm-for-continuous-gesture-and-sign-language-recognition) suggests raw pixels may matter when landmarks are unreliable.

### Phase 1c — Evaluation gate

- Score the trained head against Hand_AI v2.2 heuristics on the existing 12 photos (the v2.1/v2.2 grill set). Same gestures, same scoring rubric.
- Score against a held-out synthetic test set too — should be near-perfect; if not, the training pipeline has a bug.
- Run on a small new set of fresh phone photos to test for generalization vs. synthetic-only overfitting.

### Go/no-go

- **Beats v2.2 clearly →** proceed to Phase 2.
- **Ties or beats on some classes, loses on others →** iterate on Phase 1a (more pose diversity, more renders, more aug) before declaring failure. Two-three iteration loops before considering Phase 2 alternatives.
- **Worse than v2.2 →** debug. Most likely cause: pose distribution mismatch or insufficient mobile-camera-artifact aug. If three iterations don't close the gap, the synthetic-only hypothesis is wrong — fall back to a hybrid plan with real captures earlier.

## Phase 2 — Ship synthetic-trained Hand_AI v3

**Goal:** Replace Hand_AI's heuristic classifier with the Phase 1 learned model in production.

- Quantize/export the trained head to a format Hand_AI's browser bundle can consume. For an MLP on landmarks, TF.js or ONNX Web both work; the bundle stays small.
- Run the v2.1/v2.2-style grill rounds on the new classifier — same photo discipline as before, document failure modes.
- Wire to the existing Hand_AI gesture event system. Keep heuristics as a fallback path behind a flag for the first release in case the learned model has unexpected regressions.
- Update [Hand_AI AGENT_NOTES.md](https://github.com/warrenrross/Hand_AI/blob/main/AGENT_NOTES.md) with the v3 architecture; cross-link back to this roadmap.

**Why ship before personal capture:** ensures the baseline is stable, the inference path is proven, the gesture event integration is solid, and there's a clearly-better-than-v2.2 product in the world before asking players to invest capture time.

## Phase 3 — Per-player 3D capture tool (the splat side)

**Goal:** Let a Hand_AI player capture a low-grade 3D representation of their own hand in each of the key game poses, used to fine-tune the v3 model for that player.

### Phase 3a — Decide the capture mechanism

The realistic option set, in order of decreasing maturity:

1. **Held-pose static splat per gesture.** Player rests forearm on a table, makes the pose, holds it, orbits the phone around it for 30 seconds. Server fits MANO + 3DGS using existing tooling ([Polycam](https://poly.cam/tools/gaussian-splatting), [Luma](https://lumalabs.ai/interactive-scenes/), or self-hosted [OpenSplat](https://github.com/pierotofy/OpenSplat) / [nerfstudio gsplat](https://github.com/nerfstudio-project/gsplat)). One scan per pose × ~6 poses = ~3 minutes of capture time per player. [Details.](./gaussian-splats.md#what-works-off-the-shelf-today)
2. **Articulating capture via [HandSplat](https://arxiv.org/html/2503.14736v1) / [GraG](https://aidilayce.github.io/GraG-page/).** Player moves their hand naturally on video; server reconstructs the articulated splat. Currently research-grade only ([details](./gaussian-splats.md#what-the-research-is-doing-about-moving-hands)) — flag this as a thing to revisit in 6–12 months.
3. **Multi-photo capture without splats.** Player takes 10–20 still photos of each pose; server uses these directly as training images, plus MANO fitting for landmarks. Simpler, cheaper, but doesn't get the re-rendering-multiplier benefit.

**Default recommendation:** option 1 for v1. Option 2 is the future state, option 3 is the backup if splat fitting is too costly per user.

### Phase 3b — Build the capture web app

Architecture sketched in [mobile-capture-pipeline](./mobile-capture-pipeline.md), specialized for the per-player case:

- Mobile-friendly web app (no app store). [`getUserMedia`](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/getUserMedia) for camera.
- Guides the player through each of Hand_AI's gestures with reference visuals and capture prompts.
- For each gesture: records a ~30-second orbit video. Uploads to VPS.
- Status page so the player can see when their personalized model is ready.

### Phase 3c — VPS personalization pipeline

- Receive uploaded orbit videos.
- Run MANO + splat fitting per pose to produce a per-player 3D asset per gesture (~6 splats per player).
- Re-render each splat under randomized backgrounds and lighting → produces N synthetic training images per pose, anchored to *this player's actual hand*.
- Combine with the Phase 1 synthetic corpus and fine-tune the v3 classifier head. Save the fine-tuned weights as a per-player model.
- Make weights downloadable / deliverable to that player's Hand_AI session.

### Phase 3d — Player-side personalization toggle

- Hand_AI gains a "use my custom model" setting that loads the player's personalized weights instead of the default v3 model.
- Probably keyed to some lightweight account / token system, since model files are per-player. Open design question for later — see [open-questions.md §v1 scope](./open-questions.md#v1-scope).

### Go/no-go

- **Personalized model meaningfully outperforms v3 baseline for the same player's hand →** ship Phase 3 to players who opt in.
- **No measurable improvement →** the synthetic baseline already covers their distribution; capture tool is solving a problem that doesn't exist. Park it.

## Phase 4 — Opt-in dataset contribution *(distant, optional)*

**Only after Phase 3 is shipped and working.** If players are already capturing splats for personalization, adding an opt-in consent flow to contribute their captures to a broader dataset is cheap. But this introduces all the consent / biometric / licensing issues called out in [open-questions](./open-questions.md), and the player gets nothing extra in return — so this is not the primary motivation.

Frame this as "you've already trained your custom model, would you like to contribute anonymously to make Hand_AI better for others?" — strictly opt-in, with clear withdrawal mechanics. Probably needs real legal input before turning on.

## Risks and dependencies

| Risk | Affects | Mitigation |
|---|---|---|
| Phase 0 reveals the canned model + Model Maker already covers the need | Phases 1–4 | Park dataset-capture project; switch to integrating Gesture Recognizer + Model Maker. Phase 0 explicitly catches this. |
| HandSynthesis pipeline doesn't generalize to gesture-recognition task | Phase 1 | The paper benchmarks pose estimation, not gesture classification. Mitigation: Phase 1c evaluates explicitly on Hand_AI's actual task, with early kill criterion. |
| MANO/NIMBLE licensing blocks downstream release | Phases 1–4 if dataset is ever released; not blocking for personal Hand_AI use | See [open-questions §license math](./open-questions.md#license-math). For personal/research use only, less constrained. |
| Splat fitting too expensive to run per player | Phase 3 | Fall back to option 3 (multi-photo capture without splats) in Phase 3a. Cheaper, less novel, still useful. |
| Consent / biometric law issues if dataset is shared | Phase 4 only | Phase 4 is opt-in and distant. Get legal input before turning it on. |
| Volunteer capture rates too low for personalization to matter | Phase 3 | The personalization step is per-player, not crowdsourced — there is no "volunteer rate" until Phase 4. Phase 3 only requires individual players willing to do their own capture. |

## What this is *not* committing to

- A timeline. Each phase has go/no-go decisions, and Phase 0 might end the whole project.
- A specific tech stack for the VPS or capture tool beyond what's sketched in [mobile-capture-pipeline](./mobile-capture-pipeline.md).
- A gesture vocabulary expansion. Phase 1's scope is exactly Hand_AI's current vocabulary; vocab expansion is post-Phase 2 at the earliest.
- Hand_AI v2.2 going away. Heuristics remain a fallback through Phase 2; only Phase 3+ assumes v3 is the primary path.
- Any commitment to opening source the dataset or model — depends entirely on Phase 4 outcomes and the [license math](./open-questions.md#license-math).

## Open questions for Warren before this becomes a real roadmap

1. **Phase 0:** confirm Phase 0 is a real gate, not a formality. If the canned MediaPipe model wins, are you willing to park this and integrate it instead?
2. **Phase 1 vocab:** is the current Hand_AI vocab (`fist`, `pinch`, `near_pinch`, `point`, `open_palm`, `thumbs_up`) the right scope, or should Phase 1 also include some currently-unsupported gestures the game wants next?
3. **Phase 3 personalization scope:** is "per-player fine-tuned MLP head" the right granularity, or should personalization be something simpler (e.g., per-player threshold calibration on top of the shared v3 model)? The simpler option may suffice and is far less infrastructure.
4. **Account model:** Hand_AI is currently a static GitHub Pages site with no backend. Phase 3 requires user identity for personalized models. Smallest viable account system: email-only magic link? OAuth via GitHub/Google? Pure local-storage tokens with no server-side identity? Decision affects Phase 3b/c sizing significantly.
5. **Cost ceiling:** what's the rough budget envelope you're willing to put against VPS GPU time? This bounds whether Phase 3 splat fitting is even on the table vs. the option-3 fallback.

## Cross-references

- The technical-architecture spine: [`docs/dataset-architecture.md`](./dataset-architecture.md). The three-layer framing maps onto this roadmap as: Layer 1 ≈ Phase 1, Layer 2 ≈ deferred (no broad mobile capture in this plan), Layer 3 ≈ Phase 3.
- The synthetic-side tooling: [`docs/synthetic-rendering.md`](./synthetic-rendering.md).
- The splat-side feasibility constraints: [`docs/gaussian-splats.md`](./gaussian-splats.md).
- The web app + VPS sketch: [`docs/mobile-capture-pipeline.md`](./mobile-capture-pipeline.md). Note: this roadmap repurposes the mobile-web architecture for *per-player capture*, not crowdsourced dataset collection — different consent flow, different scale.
- Consent / license / scope: [`docs/open-questions.md`](./open-questions.md).
- The Hand_AI v2.2 baseline this is trying to beat: [Hand_AI AGENT_NOTES.md](https://github.com/warrenrross/Hand_AI/blob/main/AGENT_NOTES.md).
