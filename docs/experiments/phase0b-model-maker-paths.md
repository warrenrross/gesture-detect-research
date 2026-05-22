# Phase 0b — Model Maker testing paths

> **Parent:** [`docs/roadmap.md` — Phase 0](../roadmap.md#phase-0--decide-whether-to-build-any-of-this-blocking)
> **Predecessor experiment:** [`docs/experiments/phase0-gesture-recognizer.md`](./phase0-gesture-recognizer.md)
> **Architecture reference:** [`docs/architecture-classification-vs-localization.md`](../architecture-classification-vs-localization.md)

[Phase 0](./phase0-gesture-recognizer.md) ended on a mixed result: the canned MediaPipe Gesture Recognizer matched 0/12 of Hand_AI's grill-round points, but with two confounds — most photos were screenshots with HUD overlays (input quality) and the `Pointing_Up` label is a strict subset of Hand_AI's "point in any direction" (vocabulary mismatch).

The cheapest follow-up is to feed [MediaPipe Model Maker](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer) a small set of labeled images and retrain the classifier head on Hand_AI's actual gesture vocabulary, then check whether it now fires on side-on and palm-down points. Two ways to do that.

## Path A — Real photos, in-product test

**Premise:** Warren swaps the canned `gesture_recognizer.task` in Hand_AI for a Model-Maker-trained one, plays the game, sends back screenshots and a verdict.

> **Prerequisite:** "Swap into Hand_AI" is not actually a drop-in. Hand_AI today loads `HandLandmarker` only — there is no classifier head in the running game to replace. The integration work that adds a `GestureRecognizer` pipeline + A/B query param is roadmapped in [`phase0c-hand-ai-fork-roadmap.md`](./phase0c-hand-ai-fork-roadmap.md) and must land in a Hand_AI fork before this path's in-game step is possible.

### Steps

1. Warren captures ~50–200 photos per class on his own setup (same webcam, same lighting as the game), organized as:

   ```
   dataset/
     point/      ~50–200 jpgs
     pinch/      ~50–200 jpgs
     fist/       ~50–200 jpgs
     open_palm/  ~50–200 jpgs
     thumbs_up/  ~50–200 jpgs
     none/       ~50–200 jpgs   ← required by Model Maker; junk / no-gesture frames
   ```

   The [Model Maker docs](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer) require a `none` class explicitly: *"One of the label names must be `none`. The `none` label represents any gesture that isn't classified as one of the other gestures."*

2. Computer runs Model Maker on those images (Colab or local Python; ~10 min on CPU for ~1k images). Output: `gesture_recognizer.task`, a TFLite bundle.

3. Warren drops that `.task` file into the Hand_AI repo, replacing the canned model. Plays the game.

4. Warren screenshots the gesture-detection HUD on the same poses that broke v2.2 / broke the canned model. Tells Computer whether grab + destroy fire on points, pinches, etc.

### Pros

- **Tests the exact distribution the model will see in production.** Same camera, same lighting, same screen geometry — none of the sim-to-real gap.
- **No new infrastructure.** Model Maker is a `pip install`; Hand_AI already loads `.task` files.
- **Real verdict from a human playing the game**, which is the only ground truth that ultimately matters.

### Cons

- **Capture labor is on Warren.** Realistically 30–60 min of taking phone/webcam pics per class, organizing into folders.
- **Small datasets overfit easily.** 50–200 per class is the floor; if the model memorizes Warren's specific lighting and breaks for anyone else, we won't know until someone else plays.
- **Doesn't test the synthetic hypothesis.** Phase 1 depends on whether synthetic data alone can train a usable head. This path skips that question.

### Verdict it produces

"Does a learned head trained on a few hundred real photos of Warren's hand beat v2.2 heuristics in the game?" If yes → consider whether per-player capture (Phase 3) is the real shape of the project, not a synthetic dataset. If no → either the head is too small or the vocab is still wrong; debug from there.

---

## Path B — Synthetic photos, Model Maker test

**Premise:** Render labeled hand images from [HandSynthesis](https://github.com/delaprada/HandSynthesis) (or simpler: Blender + MANO), feed those to Model Maker, evaluate the resulting head on the real grill-round photos. This is a *miniature Phase 1* — same shape as the full synthetic roadmap, but using Model Maker's classifier head instead of training a custom MLP.

### Why this works at all

Model Maker's `Dataset.from_folder` runs MediaPipe HandLandmarker on every image first and trains only on the resulting landmark coordinates. So:

- The **synthetic renders need to be photorealistic enough for HandLandmarker to detect the hand.** If HandLandmarker fails on the renders, Model Maker silently drops them ([per the docs](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer): *"Any images without detected hands are omitted from the dataset"*). You'll get a small training set without realizing why.
- The **classifier learns from landmark geometry, not pixels.** That's actually good for sim-to-real: landmark coordinates are mostly invariant to lighting, texture, skin tone. As long as the synthetic poses are anatomically realistic, the landmarks Model Maker sees from synthetic renders will resemble the landmarks it sees from real photos.

This is the same insight that makes [HandSynthesis](./../synthetic-rendering.md) work: train downstream of landmarks (or with the landmark backbone in the loop) and the rendering doesn't need to be perfect, just plausible enough for HandLandmarker.

### Setup overview

```
┌─────────────────┐   ┌────────────────┐   ┌─────────────────┐   ┌────────────────┐
│ MANO pose       │──▶│ Render to RGB  │──▶│ Model Maker     │──▶│ gesture_       │
│ parameters per  │   │ via Blender or │   │ Dataset.from_   │   │ recognizer.    │
│ gesture         │   │ HandSynthesis  │   │ folder() runs   │   │ task           │
│ (point, pinch…) │   │ (~hundreds per │   │ HandLandmarker  │   │                │
└─────────────────┘   │  class)        │   │ + trains head   │   └────────────────┘
                      └────────────────┘   └─────────────────┘
                              │                     │
                              ▼                     ▼
                  domain randomization       evaluate on the 12
                  (lighting, backgrounds,    real grill-round
                  camera, occlusion)         photos as held-out
```

### Concrete steps

#### 1. Set up a workstation

The cloud sandbox Computer used for Phase 0 won't cut it for synthetic rendering — Blender and HandSynthesis want a GPU, a real filesystem, and probably ~50 GB free. Options:

- **Warren's local machine** if it has an NVIDIA GPU (CUDA) or an Apple Silicon Mac (Blender's Metal backend works for small batches).
- **A rented GPU box** (Vast.ai, Lambda, RunPod) for a few dollars/hour. Spin up an Ubuntu 22.04 image with CUDA 12 pre-installed.

Minimum specs: 16 GB RAM, ~50 GB disk, one GPU with ≥8 GB VRAM. CPU-only Blender works but takes ~10× longer.

#### 2. Pick a rendering stack

Two options, in increasing order of effort:

**Option B1 — MANO + Blender (custom):** Use the [MANO model](https://mano.is.tue.mpg.de/) (free for non-commercial research) loaded into Blender via the [mano-py](https://github.com/otaheri/MANO) or [SMPL-X Blender add-on](https://smpl-x.is.tue.mpg.de/). You author pose parameters per gesture, randomize lighting/HDRIs/cameras, render. Less infrastructure, more authoring per gesture.

**Option B2 — HandSynthesis (recommended):** Clone [delaprada/HandSynthesis](https://github.com/delaprada/HandSynthesis). Their CVPR 2025 paper already did the work of identifying which renders transfer (NIMBLE textures, ~300 HDRI scenes, amplitude-spectrum augmentation, forearm included). Their config files set up most of the domain randomization for you. You'll need to modify their pose distribution to match Hand_AI's gesture vocabulary instead of their default grasp poses.

Either way, the output is a folder of jpgs/pngs and per-image label metadata.

#### 3. Render the gesture set

Target rough numbers:

| Class | Render count | Pose strategy |
|---|---|---|
| `point` | ~500 | Index extended; vary roll, pitch, yaw of wrist across full sphere; vary which way the finger points; include side-on and palm-down. |
| `pinch` | ~500 | Thumb tip + index tip near contact (distance ≤ ~1 cm in MANO units); other fingers curled. |
| `near_pinch` | ~500 | Same as pinch but distance 1–3 cm. The class Hand_AI's v2.2 thumb-tuck tiebreaker exists for. |
| `fist` | ~500 | All four fingers curled into palm; thumb either across or alongside. |
| `open_palm` | ~500 | All five fingers extended; vary spread. |
| `thumbs_up` | ~500 | Fist with thumb extended upward (in world frame). |
| `none` | ~500 | Random partial poses, ambiguous mid-transitions, hands clearly not making any of the above. Required by Model Maker. |

~3,500 images total. On a single GPU at ~1 s/render, that's about an hour. Multiply by 3–5× if you iterate.

For each, randomize: camera distance (selfie range, 30–80 cm), camera roll, HDRI lighting, background composite, slight motion blur, slight Gaussian noise, JPEG compression to match mobile-camera artifacts. The [synthetic-rendering doc](../synthetic-rendering.md) summarizes which of these knobs the HandSynthesis ablations say matter most.

#### 4. Sanity check that HandLandmarker fires on the renders

**Critical step.** Run HandLandmarker on a sample of ~50 renders and check the detection rate. If it's below ~90%, the renders aren't photorealistic enough and Model Maker will silently train on a tiny subset of your data. Iterate on textures/lighting/occlusion until landmark detection is reliable.

Computer's existing `probe_handlandmarker.py` from [`tests/phase0-gesture-recognizer/`](../../tests/phase0-gesture-recognizer/) is the right tool — point it at the render directory.

#### 5. Train via Model Maker

Roughly:

```python
from mediapipe_model_maker import gesture_recognizer

data = gesture_recognizer.Dataset.from_folder(
    dirname="renders/",                       # the folder of class subdirs
    hparams=gesture_recognizer.HandDataPreprocessingParams(
        min_detection_confidence=0.5,
        shuffle=True,
    ),
)
train_data, rest = data.split(0.8)
val_data, test_data = rest.split(0.5)

hparams = gesture_recognizer.HParams(
    export_dir="exported_model",
    learning_rate=0.001,
    batch_size=32,
    epochs=10,
)
options = gesture_recognizer.GestureRecognizerOptions(hparams=hparams)
model = gesture_recognizer.GestureRecognizer.create(
    train_data=train_data,
    validation_data=val_data,
    options=options,
)

loss, acc = model.evaluate(test_data, batch_size=1)
print(f"Synthetic-held-out test: loss={loss}, acc={acc}")
model.export_model()  # writes exported_model/gesture_recognizer.task
```

Expected synthetic-held-out accuracy: very high (≥95%). If it's not, the training pipeline has a bug — the synthetic test set is in-distribution by construction.

#### 6. Evaluate on the 12 real grill-round photos

This is the actual test. Load the exported `gesture_recognizer.task` and re-run [`tests/phase0-gesture-recognizer/scripts/run_experiment.py`](../../tests/phase0-gesture-recognizer/scripts/run_experiment.py), but pointed at the new model file.

The result we care about:

| Photo set | What we want to see |
|---|---|
| 12 grill-round photos (real) | `point` fires on all 12 (or at least the 3 where Phase 0 found landmarks). |
| Synthetic-held-out test | ≥95% accuracy. If yes, the head learned the vocabulary. If no, the training is broken. |

The gap between these two numbers is the **sim-to-real gap** — the actual question Phase 1 exists to answer. If both numbers are high, the synthetic-first plan has legs. If the synthetic number is high and real is low, we know exactly where the failure is (domain shift) and can iterate.

#### 7. Optional — try it in the game

Drop the `.task` into Hand_AI, play, screenshot. Same as Path A's step 4, but with a model trained on free synthetic data instead of hand-captured real data.

### Pros

- **Tests the entire Phase 1 thesis at miniature scale** before committing to render 100k+ images or build any mobile-capture infrastructure.
- **No human labor for data labeling.** Synthetic renders come with perfect ground truth.
- **Honest dry run of the sim-to-real gap.** The number that comes out of step 6 is the most informative single data point this whole research repo has produced so far.
- **Reusable.** The render pipeline becomes Phase 1a; Model Maker stays as the cheap-classifier baseline against which the eventual Phase 1 MLP head is compared.

### Cons

- **Real infrastructure.** Workstation with GPU + Blender + HandSynthesis dependencies. Not a one-evening project unless Blender and CUDA are already set up.
- **MANO license is non-commercial.** Fine for research and for the experiment; if Hand_AI ever ships with a model trained on MANO renders, the license needs revisiting. See [`docs/open-questions.md`](../open-questions.md).
- **Easy to fool yourself.** If HandLandmarker fails on too many renders, or the pose distribution doesn't match real-game geometry, you'll get a high synthetic-held-out score and a low real-photo score — which is *correct* information but feels like a failure. The discipline is to treat that as a positive result (we learned where the gap is) rather than retry until the numbers look good.

### Verdict it produces

"Can synthetic-only training, fed through Model Maker, produce a head that fires on the real grill-round points?" If yes → Phase 1's hypothesis is validated cheaply; commit to the full synthetic build. If no → measure the gap, decide whether to fix domain randomization or pivot to Path A's real-data approach.

---

## Recommendation

Run **Path A first**. It's a couple of hours of capture and a 10-minute training run, and it produces a direct in-game verdict on the cheapest possible learned head. It also gives Warren a baseline for whether a learned classifier in the game even *feels* better than v2.2 heuristics, which is information no amount of test-set accuracy can substitute for.

If Path A wins clearly → Phase 1's full synthetic pipeline may not be needed; the project may be a per-player capture tool (Phase 3) sitting on top of Model Maker.

If Path A is ambiguous → run **Path B** to test the sim-to-real gap. The synthetic-held-out accuracy and the real-photo accuracy together tell us whether the synthetic plan in Phase 1 is going to work at all.

Either path is more informative than Phase 0's first run was, because both produce a head trained on Hand_AI's actual vocabulary instead of relying on the canned `Pointing_Up` label.

## Pointers

- [`docs/experiments/phase0-gesture-recognizer.md`](./phase0-gesture-recognizer.md) — the run that motivated this.
- [`docs/architecture-classification-vs-localization.md`](../architecture-classification-vs-localization.md) — why this only changes "what gesture," not "where on screen."
- [`docs/synthetic-rendering.md`](../synthetic-rendering.md) — the deeper version of Path B's rendering choices.
- [`docs/roadmap.md`](../roadmap.md) — where each path fits in the larger plan.
- [MediaPipe Model Maker for Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer) — official docs for the training API.
- [HandSynthesis (delaprada)](https://github.com/delaprada/HandSynthesis) — the rendering codebase for Path B.
