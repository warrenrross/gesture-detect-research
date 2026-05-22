# Synthetic hand rendering — MANO, NIMBLE, DART, HandSynthesis

> **Parent:** [RESEARCH.md §8](../RESEARCH.md#8-custom-dataset-capture--concept-and-components)
> **See also:** [`docs/experiments/phase0b-model-maker-paths.md`](./experiments/phase0b-model-maker-paths.md) — Path B applies a miniature version of this rendering pipeline to feed MediaPipe Model Maker, as a cheap dry run for Phase 1's sim-to-real gap.
> **Position in architecture:** [Layer 1 — the load-bearing one](./dataset-architecture.md#layer-1--synthetic-baseline-day-1-no-users-needed)
> **Siblings:** [dataset-architecture](./dataset-architecture.md) · [gaussian-splats](./gaussian-splats.md) · [mobile-capture-pipeline](./mobile-capture-pipeline.md) · [open-questions](./open-questions.md)

The synthetic-data side of the dataset-capture concept has matured much more than expected. Three pipelines worth knowing, in order of increasing usefulness for this project.

## MANO — the foundational rig

- **[MANO](https://mano.is.tue.mpg.de)** (Romero, Tzionas, Black, SIGGRAPH Asia 2017) — the standard parametric hand model. 778 vertices, 1,538 faces, learned from ~1000 high-resolution scans of 31 subjects.
- Pose is parameterized as joint rotations driven through linear blend skinning. Shape is a low-dimensional manifold from PCA over the scan subjects.
- Free for research; commercial use requires separate licensing — see [open-questions](./open-questions.md#license-math).
- **Why it matters here:** every modern hand-pose paper, every synthetic dataset, and every monocular hand-splat method (HandSplat, BIGS, GraG — see [gaussian-splats](./gaussian-splats.md)) is anchored to MANO. It's the shared language.

## DART — MANO + textures + accessories, ready to render

[DART](https://dart2022.github.io) (Gao et al., NeurIPS 2022) is the most directly usable thing for the v1 of this project. It extends MANO with:

- **325 hand-crafted texture maps** — skin tones, blemishes, scars, moles, tattoos, makeup
- **50 daily 3D accessories** — rings, watches, sleeves, gloves — applied to ~25% of renders
- A **Unity GUI** (`Hand.exe`) where you set pose, camera, background, lighting, and accessory
- A pre-built **[DARTset](https://dart2022.github.io)**: **800K rendered images** with perfect-aligned 3D labels (MANO pose + 21 2D/3D keypoints + vertex locations)
- Output format: 384×384 with background, or 512×512 RGBA without

You can literally download an 800K-image labeled hand dataset right now and start training. The catch: DART uses Unity (not Blender) and the GUI flow may not scale to fully scripted batch generation as cleanly as the HandSynthesis pipeline below.

## HandSynthesis (CVPR 2025) — the most important paper for this project

[github.com/delaprada/HandSynthesis](https://github.com/delaprada/HandSynthesis) — "Analyzing the Synthetic-to-Real Domain Gap in 3D Hand Pose Estimation" ([arXiv 2503.19307](https://arxiv.org/html/2503.19307v1))

The authors built a Blender + Cycles pipeline using the **NIMBLE** hand model (a higher-detail MANO descendant: 5,990 vertices and 9,984 faces vs. MANO's 778/1,538) and ablated every component of the sim-to-real gap. **Headline result:**

- Synthetic-only training reaches **84%, 91%, 88%, 91%, and 97%** of real-data performance across five different hand-pose models (simpleHand, CMR, METRO, MeshGraphormer, S²HAND) on FreiHAND
- On reduced Dex-YCB: synthetic-only matches real-data within noise (**0.87 cm vs. 0.86 cm** PA-MPJPE)
- Rendering cost: **~1 second per image** on a single RTX A5000

Code, data, and pipeline are released. This is the right v1 target.

### What actually matters (CVPR 2025 ablations)

The paper's most useful contribution is telling you **what to spend GPU on and what to skip**:

| Factor | Verdict | Notes |
|---|---|---|
| **Background and hand texture diversity** | Matters, but plateaus | ~300 HDRI scenes is enough (50% of their full asset set). More is wasted. |
| **Amplitude spectrum augmentation** | **Crucial** | Simple FFT-based aug. Synthetic and real images have different frequency statistics; this closes most of that gap. |
| **Forearm inclusion** | **Crucial** | Models locate the wrist from arm context. Floating-hand renders measurably hurt accuracy. |
| **Object occlusion priors** | Helps | Composite real arm/object regions into renders. Improves generalization. |
| **Pose distribution alignment** | Important | Use a *subset of real-world poses* to drive synthesis. Matching the target distribution > more poses. |
| **Skeleton topology adaptation** | Easy to miss; costs you | Different datasets use different joint conventions. Without label adaptation, error rises **1.02 cm → 1.28 cm**. |
| **More poses past a threshold** | Plateaus | Same plateau behavior as backgrounds. |

The strategic implication: **diversity beats photorealism**. Throwing GPU at fancier skin shaders is the wrong investment. Aggressively randomized middling-fidelity renders win.

This is also why the [NVIDIA Structured Domain Randomization](https://developer.nvidia.com/blog/structured-domain-randomization-makes-deep-learning-more-accessible/) findings transfer cleanly — same principle, different domain.

## Other synthetic hand datasets worth knowing

For prior-art context and possible augmentation sources:

- **[ObMan](https://www.di.ens.fr/willow/research/obman/data/)** (Hasson et al., CVPR 2019) — large-scale synthetic hands grasping ShapeNet objects. Body poses from MoCap, hand poses from the GraspIt robotic-grasp software. Renders SMPL+H (MANO attached to a body). Useful for hand-object-interaction priors.
- **[RHD / GANerated Hands]** — earlier-generation synthetic-or-augmented hand datasets, less useful now that DART and HandSynthesis exist but cited heavily in older sim-to-real papers.
- **[T3DGesture](https://openaccess.thecvf.com/content/ICCV2025W/DataCV/papers/Zhang_Synthetic_Hands_Meet_Legacy_Data_A_Synthetic_Dataset_for_Structured_ICCVW_2025_paper.pdf)** (ICCV 2025 workshop) — synthetic gesture dataset spanning RGB-D, point clouds, meshes, 3D keypoints, with controlled factor-isolation for benchmarking. More gesture-recognition focused than pose-estimation focused — closer to Hand_AI's actual use case than HandSynthesis is.

## Why MANO rendering vs. real capture (cooperatively)

See [dataset-architecture.md](./dataset-architecture.md) for the full side-by-side. The short version:

- **Synthetic gets infinite labeled volume cheaply, but has a known sim-to-real gap** (closing to 84–97% per HandSynthesis).
- **Real capture closes the residual gap** by providing the actual phone-camera artifacts and demographic variation synthetic can't easily fake.
- Both are needed because each is weak where the other is strong. Not because one will replace the other.

## Practical roadmap notes

If this work proceeds:

1. **First spike:** clone HandSynthesis, render a small batch (say, 10K images) of Hand_AI's current gesture set (open palm, point, peace, thumbs up, etc.), train a tiny MLP head on landmarks à la [kinivi](https://github.com/kinivi/hand-gesture-recognition-mediapipe), and see if it beats the v2.2 heuristics on the existing 12-photo grill set. If yes, the synthetic-only path has legs.
2. **Open question:** does HandSynthesis's pose distribution cover the gestures Hand_AI actually wants, or do we need to author custom MANO pose parameters? The paper uses FreiHAND/Dex-YCB pose distributions, which are grasp-heavy, not gesture-heavy.
3. **License hygiene:** MANO is research-only by default; NIMBLE has its own terms — see [open-questions](./open-questions.md#license-math) before any dataset gets released publicly.

## Cross-references

- The model upgrade paths these synthetic data would feed: [RESEARCH.md §7](../RESEARCH.md#7-open-questions--tbd-for-warren) (static MLP head vs. temporal LSTM).
- The pretrained models that could consume this data: [RESEARCH.md §6.2](../RESEARCH.md#62-pretrained-open-weight-models).
- The mobile-camera reality this would need to be paired with: [mobile-capture-pipeline](./mobile-capture-pipeline.md).
