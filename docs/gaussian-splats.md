# Gaussian splats for hand assets

> **Parent:** [RESEARCH.md §8](../RESEARCH.md#8-custom-dataset-capture--concept-and-components)
> **Position in architecture:** [Layer 3 — the "personal long-tail" multiplier](./dataset-architecture.md#layer-3--static-splats-as-the-personal-long-tail-layer)
> **Siblings:** [dataset-architecture](./dataset-architecture.md) · [synthetic-rendering](./synthetic-rendering.md) · [mobile-capture-pipeline](./mobile-capture-pipeline.md) · [open-questions](./open-questions.md)

## What we're not talking about

The music-video and VFX-stage splat captures ([Superman's Deus stage at Infinite Realities](https://ir-ltd.net), ASAP Rocky's "Helicopter" at [Evercoast](https://evercoast.com)) are the wrong reference class. Those productions use 56–192 synchronized cameras and produce terabytes of raw footage per capture session. Not applicable to a mobile-web + VPS architecture.

The right reference class: **a 30-second phone-video orbit producing a low-grade but usable 3D asset of one person's hand.**

## What works off-the-shelf today

The Polycam / Luma / Scaniverse path is mature for **static objects**:

- Input: 15–60 second phone video (slow-mo recommended, minimal blur), or 20–200 still photos covering all angles
- Processing: 20–30 minutes in the cloud
- Output: a downloadable [Splat PLY](https://www.reddit.com/r/VisionPro/comments/1f0ea5d/tutorial_how_to_scan_your_own_gaussian_splats/) (note: not regular PLY — "Splat PLY")
- Polycam's own [guidance](https://poly.cam/tools/gaussian-splatting): full orbit around the subject, uniform lighting, no panning/tilting/zooming, move legs not wrist

### The killer constraint, buried in every tutorial

From the [VisionPro tutorial](https://www.reddit.com/r/VisionPro/comments/1f0ea5d/tutorial_how_to_scan_your_own_gaussian_splats/):

> The object you want to scan **must not move during the scan.** Any movement of the object will result in ghosting in the final output.

For a hand, this means:

- ✅ **Held pose is scannable today.** Volunteer makes a fist, rests their forearm on a table, the other hand orbits a phone around it for 30 seconds → workable static splat of that one gesture, on that one person.
- ❌ **Articulating hand is not.** A natural finger-curl, a wave, anything dynamic — consumer tools produce ghosted garbage.

So with zero custom code, the realistic v1 is a **library of frozen gestures** per volunteer: maybe 1–3 minutes of capture time per pose, yielding one re-renderable splat per pose per individual.

## What the research is doing about moving hands

There's a clear 2024–2026 academic lineage purpose-built for monocular video of an articulating hand. The relevant landmarks:

### [GauHuman](https://github.com/skhu101/GauHuman) (CVPR 2024)

- Articulated body splats from monocular video
- **1–2 min training, 154–189 FPS rendering** — fast enough to actually consider
- Code is open
- It's a *body* model (anchored to SMPL), not a hand model, but the architecture template — Gaussians anchored to a parametric mesh, driven by linear blend skinning — is what everyone else copies.

### [HandSplat](https://arxiv.org/html/2503.14736v1) (March 2025)

- Anchors Gaussians to **MANO** hand-model vertices and adds learnable embeddings for non-rigid skin/wrinkle motion
- Includes pose-conditioned attribute regularization and a lightweight attention mechanism for geometry/appearance fusion
- Code is "to be released upon acceptance" — last confirmed status: not posted yet
- Trained on **[InterHand2.6M](https://mks0601.github.io/InterHand2.6M/)** — a *multi-view lab* dataset, not in-the-wild monocular phone video. The transfer to phone capture is unproven.
- Training-time data point: prior work HandAvatar takes **8–30 days** to train. HandSplat doesn't publish its own training time but is positioned as faster.

### [BIGS](https://github.com/On-JungWoan) (CVPR 2025)

- Bimanual hand + object reconstruction from a single monocular video
- Shares a single Gaussian set across both hands to accumulate 3D info from limited views
- Uses SDS (score distillation sampling) loss with a pre-trained diffusion model to fill in unseen object parts
- MANO-anchored

### [GraG — "Grasp in Gaussians"](https://aidilayce.github.io/GraG-page/)

- Explicitly targets monocular video, hand-plus-object
- Claims runtime cut from **3–10 hours → ~30 minutes** on long sequences
- Uses a compact "Sum-of-Gaussians" representation revived from classical tracking literature
- Project page is up; code status unclear

### The sobering counterpoint

[Liang et al. (arXiv 2412.04457)](https://arxiv.org/html/2412.04457v2) — "Monocular Dynamic Gaussian Splatting: Fast, Brittle, and Scene Complexity Rules" — benchmarks all these monocular dynamic methods and concludes they are:

- **"Fast and brittle"** — Gaussian methods render at 20–200 FPS vs. 0.3 FPS for older NeRF methods, but optimization is much less stable
- **Worse than NeRF-style TiNeuVox on quality** for strictly monocular dynamic scenes (across all metrics except LPIPS)
- **Sensitive to camera baseline and motion magnitude** — narrow baselines (phone in one hand orbiting) and fast object motion (an articulating hand) are exactly the failure modes
- Training times of **1.5–4 hours per sequence** on their benchmarks, not minutes

Translation: **research-grade, not product-grade.** Worth tracking the GauHuman → HandSplat → GraG lineage; do not bet v1 on it.

## What this means for the architecture

See [dataset-architecture.md Layer 3](./dataset-architecture.md#layer-3--static-splats-as-the-personal-long-tail-layer) for the role in the full pipeline.

**Pragmatic v1 use:** static splats only. Volunteer captures a held pose, server fits MANO + a static splat, then synthesizes many re-rendered views of *that specific individual's hand* in arbitrary lighting and backgrounds.

**Why this is uniquely valuable:** the splat captures **real skin realism for one individual** that the [synthetic pipeline](./synthetic-rendering.md) can't fake well — particularly skin tones, hair, scars, and texture detail underrepresented in MANO/NIMBLE's source scans. It's a per-volunteer "skin" pluggable into the synthetic renderer.

**What it doesn't do:** motion. Don't expect this to capture gesture *dynamics*. That's still the [synthetic rendering layer's](./synthetic-rendering.md) job, plus whatever real video the [mobile capture pipeline](./mobile-capture-pipeline.md) collects.

## A standing question

[NVIDIA's SDR work](https://developer.nvidia.com/blog/structured-domain-randomization-makes-deep-learning-more-accessible/) and the [HandSynthesis CVPR 2025 ablations](./synthetic-rendering.md#what-actually-matters-cvpr-2025-ablations) both point to the same conclusion: **diversity matters more than realism**. If true at scale, optimizing for splat photorealism might be the wrong axis to push on. The argument for splats over more aggressive randomization rests on: (a) demographic skin realism that randomization can't cheaply produce, and (b) per-individual identity for downstream evaluation. Whether (a) and (b) are worth the infra cost is a Layer-3 decision that can be deferred until Layers 1+2 are running.

## Compression and tooling notes

- **[Niantic SPZ](https://github.com/nianticlabs/spz)** — 10× smaller than raw PLY, recently adopted into the glTF standard. The default modern splat format.
- **MetalSplatter / SuperSplat / PostShot** — viewer/editor tooling. Mostly relevant if humans review captures.
- **OTOY [Octane Render](https://home.otoy.com/render/octane-render/)** — first commercial path tracer that natively renders and relights Gaussian splats. Probably overkill for this project but useful if the rendering side ever wants relighting.
- **[Polycam](https://poly.cam/tools/gaussian-splatting)** — cloud splat service. Reasonable v1 if we don't want to run our own splat optimizer.
- **[OpenSplat](https://github.com/pierotofy/OpenSplat)** / **[nerfstudio gsplat](https://github.com/nerfstudio-project/gsplat)** — open-source splat trainers if we self-host.
