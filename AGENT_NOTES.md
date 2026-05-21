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

1. **Build a roadmap** for what comes after Phase 1 research. This is the explicit blocker for everything else.
2. **Cheap experiment from `RESEARCH.md` §7:** run the canned MediaPipe Gesture Recognizer head-to-head against Hand_AI v2.2 heuristics on the same 12 photos from the v2.1/v2.2 grill rounds. Would clarify whether we're reinventing or outperforming.
3. **Try HaGRIDv2** (`RESEARCH.md` §6.1 row 2) on Hand_AI's failure cases to see how the public state of the art handles palm-down foreshortening.
4. **Capture-tool design.** Eventually this repo houses software to gather labeled gesture data. The decision deferred today: Python (matches ML tooling) or web (matches Hand_AI). Likely both — web for capture, Python for evaluation.

## Sibling repos and where they fit

- [Hand_AI](https://github.com/warrenrross/Hand_AI) — primary consumer of whatever model emerges. Default branch `main`. v2.2 is current; gesture vocab is fist / pinch / point / open_palm / thumbs_up.
- [JS-Image-Classifier](https://github.com/warrenrross/JS-Image-Classifier) — MobileNet+KNN sibling. Default branch `master`. May consume.
- [warrenrross.github.io](https://github.com/warrenrross/warrenrross.github.io) — has the ADRs and CONTEXT.md. ADR-0002 covers the two-sibling-classifier-repos split.
- [thehandtrick](https://github.com/warrenrross/thehandtrick) — 2019 ancestor. Default branch `master`. Documented in `RESEARCH.md` §2 for historical reference.

## Status

Phase 1 (research) ongoing. No PRs yet. Initial commit creates `RESEARCH.md`, this file, `README.md`, `LICENSE`, `.gitignore`.
