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

**The spine recommendation across all docs:** build synthetic-first (Layer 1), then mobile capture (Layer 2), then splats (Layer 3 or never). Each layer is independently useful and fails gracefully. **But run the cheap experiment from §7 first** — test Google's Gesture Recognizer head-to-head against v2.2 heuristics before committing to dataset capture at all.

## Active design rules (carried over from Hand_AI)

These conventions apply across both repos:

- **GitHub via `gh` CLI**, never browser_task. Use `api_credentials=["github"]`. Credentials are pre-configured — do not run `gh auth status` or inspect them.
- **Default branch is `main`**, not master.
- **Agent opens AND merges PRs** — squash + delete branch.
- **One question at a time when grilling.** Walk down the design tree, surface contradictions immediately, cross-reference code (when there is code).
- **Cite sources for any thresholds, model claims, or dataset stats.** Every section of `RESEARCH.md` follows this. Maintain the standard.
- **White-space between gestures** (Hand_AI design principle). Will likely also apply to any learned model — don't fire a gesture just because another didn't.

## Likely next steps (not committed)

These are the threads Warren left open, not a roadmap. Pick whichever is in scope when the session starts:

1. **Build a roadmap** for what comes after Phase 1 research. This is the explicit blocker for everything else. The §8 architecture and `docs/` wiki are now an input to that roadmap conversation, not a substitute.
2. **Run the cheap experiment from `RESEARCH.md` §7** — canned MediaPipe Gesture Recognizer vs. Hand_AI v2.2 heuristics on the 12 grill-round photos. Per [`docs/open-questions.md`](./docs/open-questions.md#sequencing--what-to-build-first), this is the highest-leverage thing to do *before* committing to dataset capture, because if heuristics tie/win the whole capture project may be solving the wrong problem.
3. **First synthetic spike:** per [`docs/synthetic-rendering.md`](./docs/synthetic-rendering.md#practical-roadmap-notes), clone HandSynthesis, render ~10K images of Hand_AI's current gesture set, train an MLP head on landmarks, evaluate against v2.2 heuristics. Tests whether the synthetic-only path has legs without any mobile-web infrastructure.
4. **Try HaGRIDv2** (`RESEARCH.md` §6.1 row 2) on Hand_AI's failure cases to see how the public state of the art handles palm-down foreshortening.
5. **Capture-tool design.** If/when this proceeds, the architecture is sketched in [`docs/mobile-capture-pipeline.md`](./docs/mobile-capture-pipeline.md). Open decisions before any code: consent UX, account-vs-anonymous, gesture vocabulary scope, license for the resulting dataset (see [`docs/open-questions.md`](./docs/open-questions.md)).

## Sibling repos and where they fit

- [Hand_AI](https://github.com/warrenrross/Hand_AI) — primary consumer of whatever model emerges. Default branch `main`. v2.2 is current; gesture vocab is fist / pinch / point / open_palm / thumbs_up.
- [JS-Image-Classifier](https://github.com/warrenrross/JS-Image-Classifier) — MobileNet+KNN sibling. Default branch `master`. May consume.
- [warrenrross.github.io](https://github.com/warrenrross/warrenrross.github.io) — has the ADRs and CONTEXT.md. ADR-0002 covers the two-sibling-classifier-repos split.
- [thehandtrick](https://github.com/warrenrross/thehandtrick) — 2019 ancestor. Default branch `master`. Documented in `RESEARCH.md` §2 for historical reference.

## Status

Phase 1 (research) ongoing. No PRs yet. Initial commit creates `RESEARCH.md`, this file, `README.md`, `LICENSE`, `.gitignore`.
