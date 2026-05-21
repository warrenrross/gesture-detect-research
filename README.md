# gesture-detect-research

Research repo for the next generation of hand-gesture detection in [Hand_AI](https://github.com/warrenrross/Hand_AI) and adjacent projects.

## What this repo is

A working space for figuring out *what comes after* hand-tuned threshold heuristics. Documents the dataset landscape, the open-weight model landscape, and the upgrade paths under consideration. Will eventually house:

- Software to **gather labeled gesture data** (a custom dataset captured under the conditions Hand_AI actually runs in — mobile cameras, varied lighting, palm-side and palm-down hands).
- **Evaluations** of pretrained models (MediaPipe Gesture Recognizer, kinivi/Kazuhito00 MLP, Handtrack.js, OpenPose hand) head-to-head on the same inputs Hand_AI struggles with.
- The **custom dataset** itself, once captured.
- **Notebooks and scripts** for ad-hoc exploration.

## What this repo is not

- Not a fork of Hand_AI. Hand_AI ships a working browser app; this repo is upstream of any future model that might replace its heuristics.
- Not yet a software project. No build, no package, no folder commitments. Those decisions wait until the research surfaces a clear direction. See [`AGENT_NOTES.md`](./AGENT_NOTES.md) for why we deferred a full scaffold.

## Where to start

- **[`RESEARCH.md`](./RESEARCH.md)** — the main artifact. Covers:
  - §1–3: model lineage from `thehandtrick` (Handtrack.js / EgoHands) through current Hand_AI (MediaPipe HandLandmarker).
  - §4: six follow-on threads, including the registerable-embedding pattern (FingerNet) and the MediaPipe + LSTM family.
  - §5: the academic parent (OpenPose / CMU Panoptic).
  - §6: datasets and pretrained models actually grabbable today.
  - §7: open questions on upgrade-path direction.
  - §8: custom dataset capture concept — entry point into the [`docs/`](./docs/) wiki below.
- **[`docs/`](./docs/)** — topic-scoped supplemental docs in a Karpathy-style wiki layout. Each doc links to its parent (RESEARCH.md §8) and its siblings. See the index below.
- **[`AGENT_NOTES.md`](./AGENT_NOTES.md)** — session-to-session handoff notes, matches the convention in [Hand_AI](https://github.com/warrenrross/Hand_AI/blob/main/AGENT_NOTES.md).

## Docs index

Supplemental documents under [`docs/`](./docs/), all anchored in [RESEARCH.md §8](./RESEARCH.md#8-custom-dataset-capture--concept-and-components):

| Doc | Scope |
|---|---|
| [`docs/dataset-architecture.md`](./docs/dataset-architecture.md) | Three-layer side-by-side framing (synthetic + mobile + splats), v1 architecture, failure modes |
| [`docs/synthetic-rendering.md`](./docs/synthetic-rendering.md) | MANO / NIMBLE / DART / HandSynthesis pipelines, CVPR 2025 sim-to-real ablations |
| [`docs/gaussian-splats.md`](./docs/gaussian-splats.md) | Low-grade phone-video splats, static vs. articulating, GauHuman → HandSplat → GraG research lineage |
| [`docs/mobile-capture-pipeline.md`](./docs/mobile-capture-pipeline.md) | Web app + VPS architecture, auto-labeling strategy, compute sizing |
| [`docs/open-questions.md`](./docs/open-questions.md) | Consent / biometric data, license math, v1 scope, sequencing |
| [`docs/roadmap.md`](./docs/roadmap.md) | Starting-point roadmap: synthetic-first dataset → ship Hand_AI v3 → per-player splat capture for personalization |

## Status

**Phase 1: Research.** Survey of the landscape is captured in RESEARCH.md + `docs/`. A starting-point roadmap is now drafted in [`docs/roadmap.md`](./docs/roadmap.md) but explicitly framed as a starting point, not a commitment — Phase 0 is a gate that could end the whole project.

## Related repos

- [warrenrross/Hand_AI](https://github.com/warrenrross/Hand_AI) — the current MediaPipe-based gesture classifier (v2.2). The primary consumer of any model this research produces.
- [warrenrross/JS-Image-Classifier](https://github.com/warrenrross/JS-Image-Classifier) — sibling repo using MobileNet + KNN. May also consume.
- [warrenrross/thehandtrick](https://github.com/warrenrross/thehandtrick) — 2019 ancestor using Handtrack.js. Covered in `RESEARCH.md` §2.

## License

MIT. See [`LICENSE`](./LICENSE).
