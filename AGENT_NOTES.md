# AGENT_NOTES — gesture-detect-research

Handoff notes between agent sessions. Same convention as [Hand_AI/AGENT_NOTES.md](https://github.com/warrenrross/Hand_AI/blob/main/AGENT_NOTES.md). Read this first when picking up work.

## Why this repo exists

Hand_AI v2.2 ships a working browser-based gesture classifier built on hand-tuned thresholds over MediaPipe HandLandmarker output (see [Hand_AI/AGENT_NOTES.md](https://github.com/warrenrross/Hand_AI/blob/main/AGENT_NOTES.md) for the v2.2 design and the two photo-grill rounds that produced it). The heuristic approach hit visible limits: foreshortening artifacts on palm-down hands, ambiguity between `point` and `near_pinch`, and a Reddit caveat (cited in `RESEARCH.md` §4.6) that MediaPipe landmarks degrade on mobile cameras under poor lighting. This repo exists to research what an upgrade past hand-tuned thresholds looks like — and to build the tooling and dataset that upgrade would require.

## Current phase

**Phase 1: Research.** Surveying datasets, pretrained models, and architectural patterns. Output is `RESEARCH.md`. **No code or folder structure yet** — Warren explicitly deferred scaffolding until the research surfaces a clear direction.

> Quote, May 21 2026: *"skip the planned folders, we need to build a roadmap before that and I'm not certain what that looks like yet. The research will get us there."*

## What's in `RESEARCH.md` today

- Lineage trace: `thehandtrick` (Handtrack.js / EgoHands, 2019) → current Hand_AI (MediaPipe HandLandmarker, 2025).
- Six follow-on threads in §4, including the registerable-embedding pattern (Meng et al. 2024 / FingerNet) and the MediaPipe + LSTM family.
- §6: tables of grabbable datasets and pretrained open-weight models.
- §7: open questions framing two distinct upgrade paths — static-registerable vs temporal-LSTM.
- §8: **custom dataset capture concept** — entry point + index into the [`docs/`](./docs/) wiki. Three-layer architecture (synthetic CGI + mobile-web capture + low-grade splats).

## What's in `docs/` today (Karpathy llm-wiki style)

Supplemental docs, all anchored to RESEARCH.md §8 as their parent, with sibling cross-links between each:

- [`docs/dataset-architecture.md`](./docs/dataset-architecture.md) — three-layer side-by-side framing, v1 architecture, failure modes / graceful degradation.
- [`docs/synthetic-rendering.md`](./docs/synthetic-rendering.md) — MANO / NIMBLE / DART / HandSynthesis. **Key finding:** CVPR 2025 HandSynthesis paper shows synthetic-only training hits 84–97% of real-data accuracy. Code released at [github.com/delaprada/HandSynthesis](https://github.com/delaprada/HandSynthesis).
- [`docs/gaussian-splats.md`](./docs/gaussian-splats.md) — phone-video splats. **Key finding:** static held poses scannable today via Polycam/Luma; articulating hands are research-grade only (GauHuman → HandSplat → GraG lineage). Liang et al. benchmark calls dynamic methods "fast and brittle."
- [`docs/mobile-capture-pipeline.md`](./docs/mobile-capture-pipeline.md) — web app + VPS. **Key finding:** real role is capturing mobile-camera artifacts the synthetic pipeline can't fake; MediaPipe auto-labels handle easy cases, low-confidence frames are the gold.
- [`docs/open-questions.md`](./docs/open-questions.md) — consent / biometric law, MANO/NIMBLE license restrictions, v1 scope, sequencing.
- [`docs/roadmap.md`](./docs/roadmap.md) — **starting-point roadmap** (not finalized). Phase 0 cheap experiment → Phase 1 synthetic baseline beating v2.2 → Phase 2 ship Hand_AI v3 → Phase 3 per-player splat capture for personalization → Phase 4 optional opt-in dataset contribution. Warren's framing: synthetic-first custom dataset for Hand_AI's game, then a tool letting players capture 3D representations of their own hands to fine-tune the AI to their use.
- [`docs/experiments/phase0-gesture-recognizer.md`](./docs/experiments/phase0-gesture-recognizer.md) — **Phase 0 experiment record (May 21, 2026).** Canned MediaPipe Gesture Recognizer (`gesture_recognizer.task`, float16) run on the 12 v2.2 grill-round photos. **Result:** 0/12 `Pointing_Up` matches on raw, 0/12 on cropped (with 3/12 hands detected, all returning literal `"None"`). Hand_AI v2.2 fires POINT on all 12. **Mixed signal** — detection-failure caveat (screenshots with HUD overlays, not raw webcam frames) AND label-vocabulary mismatch (`Pointing_Up` ≠ "point in any direction"). Decision: proceed to Phase 1 cautiously; two cheap follow-ups suggested before committing to full synthetic pipeline. Reproducible bundle at [`tests/phase0-gesture-recognizer/`](./tests/phase0-gesture-recognizer/).
- [`docs/architecture-classification-vs-localization.md`](./docs/architecture-classification-vs-localization.md) — **architecture note (May 21, 2026).** Disambiguates *what gesture* (classifier head) from *where on screen* (HandLandmarker coordinates). Classifier swaps (heuristics → canned → Model Maker → Phase 1 synthetic-trained head) change only "what," never "where" — fingertip/centroid coords come from HandLandmarker upstream and are identical across every roadmap option. Written after Warren asked whether Model Maker would help with grabbing/destroying emoji locations.
- [`docs/experiments/phase0b-model-maker-paths.md`](./docs/experiments/phase0b-model-maker-paths.md) — **Phase 0b plan (not yet run).** Two paths to retrain the classifier head via MediaPipe Model Maker. **Path A:** ~50–200 real photos per class captured by Warren, train via Model Maker, drop the resulting `.task` into Hand_AI, Warren plays and reports back with screenshots. **Path B:** render hand poses with MANO/HandSynthesis (~500 per class), feed to Model Maker, evaluate on the 12 real grill-round photos as held-out — a miniature dry run of the Phase 1 sim-to-real gap. Doc includes the full Python training call, target render counts, and the critical "sanity-check that HandLandmarker fires on the renders" step (Model Maker silently drops images where HandLandmarker doesn't detect a hand). Recommendation: run Path A first; run Path B only if Path A is ambiguous. **Note:** the "drop into Hand_AI and play" step in Path A is not actually a drop-in — Hand_AI currently loads `HandLandmarker` only, with v2.2 heuristics doing all classification. The integration work needed first is spec'd in [`phase0c-hand-ai-fork-roadmap.md`](./docs/experiments/phase0c-hand-ai-fork-roadmap.md).
- [`docs/experiments/phase0c-hand-ai-fork-roadmap.md`](./docs/experiments/phase0c-hand-ai-fork-roadmap.md) — **Phase 0c plan (scheduled for next session).** Fork Hand_AI to a new repo (`Hand_AI-gesture-recognizer-experiment`), branch `phase0c-gesture-recognizer` off `main` (Hand_AI's default branch is `main`, not `master`). Modify [`assets/js/handTracker.js`](https://github.com/warrenrross/Hand_AI/blob/main/assets/js/handTracker.js) to add a parallel `GestureRecognizer` pipeline alongside the existing `HandLandmarker` (both come from `@mediapipe/tasks-vision` already imported). Modify `app.js` to accept `?classifier=heuristics|learned|both` query param — `heuristics` is the default (zero regression on live site), `learned` uses canned `Pointing_Up`-vocab labels only, `both` runs both pipelines and shows side-by-side in HUD. Enable GitHub Pages on the fork → live A/B URL at `https://warrenrross.github.io/<fork-name>/`. Warren plays with `?classifier=both` and reports back. **Original `Hand_AI` repo is untouched** until Phase 0c proves itself; promotion path (fork → PR → original) and decision rule are in the doc.

**The spine recommendation across all docs:** build synthetic-first (Layer 1), then mobile capture (Layer 2), then splats (Layer 3 or never). Each layer is independently useful and fails gracefully. **But run the cheap experiment from §7 first** — test Google's Gesture Recognizer head-to-head against v2.2 heuristics before committing to dataset capture at all. This is encoded as Phase 0 of [`docs/roadmap.md`](./docs/roadmap.md).

## Active design rules (carried over from Hand_AI)

These conventions apply across both repos:

- **GitHub via `gh` CLI**, never browser_task. Use `api_credentials=["github"]`. Credentials are pre-configured — do not run `gh auth status` or inspect them.
- **Default branch is `main`**, not master.
- **Agent opens AND merges PRs** — squash + delete branch.
- **One question at a time when grilling.** Walk down the design tree, surface contradictions immediately, cross-reference code (when there is code).
- **Cite sources for any thresholds, model claims, or dataset stats.** Every section of `RESEARCH.md` follows this. Maintain the standard.
- **White-space between gestures** (Hand_AI design principle). Will likely also apply to any learned model — don't fire a gesture just because another didn't.

## Likely next steps (not committed)

These are the threads Warren left open. Pick whichever is in scope when the session starts. **A starting-point roadmap is now drafted at [`docs/roadmap.md`](./docs/roadmap.md)** — it's framed as a starting point with explicit go/no-go gates, not a commitment. Open questions for Warren are listed in that doc's final section.

1. **Iterate on the roadmap.** [`docs/roadmap.md`](./docs/roadmap.md) is a starting point. Warren has open questions enumerated at the bottom of that doc — Phase 0 gate confirmation, Phase 1 vocab scope, Phase 3 personalization granularity, account model decision, cost ceiling.
2. **Phase 0c — Hand_AI fork with GestureRecognizer integration (NEXT SESSION).** [`docs/experiments/phase0c-hand-ai-fork-roadmap.md`](./docs/experiments/phase0c-hand-ai-fork-roadmap.md) has the full 7-step plan. This unblocks every in-game test of any learned classifier (canned, Model Maker, or Phase 1). Tomorrow's work: fork Hand_AI, add `GestureRecognizer` to `handTracker.js`, add `?classifier=` query param to `app.js`, enable Pages, hand Warren the URL. Estimated ~1–2 hours of focused Computer work; in-game testing is whatever play time Warren wants after that.
3. **Phase 0 follow-ups (after 0c).** Phase 0's first run is done ([`docs/experiments/phase0-gesture-recognizer.md`](./docs/experiments/phase0-gesture-recognizer.md)) and the mixed result has cheap follow-ups that haven't run yet. The Model Maker follow-up ([`phase0b-model-maker-paths.md`](./docs/experiments/phase0b-model-maker-paths.md)) requires the Phase 0c integration first to do its in-game test honestly. The third open follow-up: rerun the canned Gesture Recognizer on raw webcam frames (not screenshots) to isolate detection failure from classification failure — the Phase 0c fork running with `?classifier=both` produces this data as a byproduct. The reproducible sandbox bundle at [`tests/phase0-gesture-recognizer/`](./tests/phase0-gesture-recognizer/) is the starting point if a non-fork-based rerun is preferred.
4. **First synthetic spike:** per [`docs/synthetic-rendering.md`](./docs/synthetic-rendering.md#practical-roadmap-notes), clone HandSynthesis, render ~10K images of Hand_AI's current gesture set, train an MLP head on landmarks, evaluate against v2.2 heuristics. Tests whether the synthetic-only path has legs without any mobile-web infrastructure.
5. **Try HaGRIDv2** (`RESEARCH.md` §6.1 row 2) on Hand_AI's failure cases to see how the public state of the art handles palm-down foreshortening.
6. **Capture-tool design.** If/when this proceeds, the architecture is sketched in [`docs/mobile-capture-pipeline.md`](./docs/mobile-capture-pipeline.md). Open decisions before any code: consent UX, account-vs-anonymous, gesture vocabulary scope, license for the resulting dataset (see [`docs/open-questions.md`](./docs/open-questions.md)).

## Sibling repos and where they fit

- [Hand_AI](https://github.com/warrenrross/Hand_AI) — primary consumer of whatever model emerges. Default branch `main`. v2.2 is current; gesture vocab is fist / pinch / point / open_palm / thumbs_up.
- [JS-Image-Classifier](https://github.com/warrenrross/JS-Image-Classifier) — MobileNet+KNN sibling. Default branch `master`. May consume.
- [warrenrross.github.io](https://github.com/warrenrross/warrenrross.github.io) — has the ADRs and CONTEXT.md. ADR-0002 covers the two-sibling-classifier-repos split.
- [thehandtrick](https://github.com/warrenrross/thehandtrick) — 2019 ancestor. Default branch `master`. Documented in `RESEARCH.md` §2 for historical reference.

## Status

Phase 1 (research) ongoing. No PRs yet. Initial commit creates `RESEARCH.md`, this file, `README.md`, `LICENSE`, `.gitignore`.
