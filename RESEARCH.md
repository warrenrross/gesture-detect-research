# Hand_AI — Research Notes

Working document. Captures the model lineage behind Warren's two hand-tracking projects (`thehandtrick` and current `Hand_AI`), the availability of their training data and papers, and a survey of follow-on work since.

Not yet committed to the repo — held until research phase is signed off.

---

## 1. Lineage at a glance

| Project | Era | Model used | Output | Backbone |
|---|---|---|---|---|
| [warrenrross/thehandtrick](https://github.com/warrenrross/thehandtrick) (fork of [sarthology/thehandtrick](https://github.com/sarthology/thehandtrick)) | 2019 | **Handtrack.js** by Victor Dibia | Single bounding box per hand | SSD + MobileNetV1, trained on **EgoHands** |
| [warrenrross/Hand_AI](https://github.com/warrenrross/Hand_AI) (current) | 2025–26 | **MediaPipe HandLandmarker** by Google | 21 3D keypoints per hand | Two-stage: BlazePalm detector → landmark regressor |

Same problem (find a hand in a webcam frame, in the browser, in real time), two very different solutions: one returns *where* the hand is, the other returns *how it's shaped*.

---

## 2. thehandtrick lineage — Handtrack.js / EgoHands

### The model

- **Handtrack.js** ([github](https://github.com/victordibia/handtrack.js/), [TF blog](https://blog.tensorflow.org/2019/11/handtrackjs-tracking-hand-interactions.html)) — a TensorFlow.js wrapper around a model originally trained in [victordibia/handtracking](https://github.com/victordibia/handtracking).
- Architecture: **SSD (Single Shot Detector) with a MobileNetV1 backbone**, transfer-learned from `ssd_mobilenet_v1_coco` in the TensorFlow Object Detection model zoo.
- Training run: ~200,000 steps on a cloud GPU (~5 hrs), final total loss ≈ 2.575 ([repo README](https://github.com/victordibia/handtracking#training-the-hand-detection-model)).
- Output: bounding boxes only — no fingers, no pose. Good enough for "is there a hand here, where is it" interactions, which is what `thehandtrick` uses to drive a Three.js scene.

### Dataset — **EgoHands** (Indiana University)

- **Available? Yes, publicly, since 2015.**
- Source: [vision.soic.indiana.edu/egohands](http://vision.soic.indiana.edu/egohands/) (Indiana University Computer Vision Lab).
- Mirror with conversion to standard object-detection formats: [Roboflow EgoHands page](https://public.roboflow.com/object-detection/hands).
- Contents: **4,800 images, 48 first-person videos, >15,000 pixel-level hand annotations**. Filmed on Google Glass while two participants played puzzles, chess, Jenga, or cards across 48 environments.
- Labels: four classes (`myleft`, `myright`, `yourleft`, `yourright`) or one merged `hand` class. Dibia used the merged class.

### Papers

- **Dataset paper (peer-reviewed):** Bambach, Lee, Crandall, Yu. *"Lending a Hand: Detecting Hands and Recognizing Activities in Complex Egocentric Interactions."* ICCV 2015. [PDF (CVF open access)](https://openaccess.thecvf.com/content_iccv_2015/papers/Bambach_Lending_A_Hand_ICCV_2015_paper.pdf).
- **Handtrack.js "paper":** there is no peer-reviewed paper. Dibia's reference is a GitHub-hosted PDF inside the [handtracking repo](https://github.com/victordibia/handtracking) plus a [Medium walkthrough](https://medium.com/@victor.dibia/how-to-build-a-real-time-hand-detector-using-neural-networks-ssd-on-tensorflow-d6bac0e4b2ce) and a [2019 TensorFlow blog post](https://blog.tensorflow.org/2019/11/handtrackjs-tracking-hand-interactions.html). The repo README still says "a full paper will be added when complete." It hasn't been.
- Background reading Dibia cites: the original [SSD paper (Liu et al., 2016)](https://arxiv.org/abs/1512.02325) and [MobileNets (Howard et al., 2017)](https://arxiv.org/abs/1704.04861).

### What this means for `thehandtrick`

The 2019 fork inherits a model trained on **egocentric, table-top, two-player scenes** — not webcam selfies. That's why bounding-box-only worked: the use case was "is the user reaching into the frame," not "what's the user's hand doing." The dataset is small (4,800 images) and visually narrow, which is also why Dibia notes [in the repo](https://github.com/victordibia/handtracking#thoughts-on-optimization) that the detector struggles with non-egocentric viewpoints, noisy backgrounds, and unusual skin tones.

---

## 3. Hand_AI lineage — MediaPipe HandLandmarker

### The model

- **MediaPipe HandLandmarker** ([Google AI Edge docs](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker), [JS reference](https://ai.google.dev/edge/api/mediapipe/js/tasks-vision.handlandmarkeroptions)) — Google's two-stage pipeline:
  1. **BlazePalm detector** finds the palm's oriented bounding box. Detecting palms (rigid, ~square) is easier than detecting full hands (articulated, varied aspect ratios).
  2. **Hand landmark regressor** predicts **21 3D keypoints** inside that cropped region. The detector only re-fires when tracking is lost, so on most frames only the cheap landmark model runs.
- This is what `Hand_AI` consumes via the Tasks Vision JS package (pinned to `@mediapipe/tasks-vision@0.10.14` in [assets/js/handTracker.js](https://github.com/warrenrross/Hand_AI/blob/main/assets/js/handTracker.js)).

### Dataset — **proprietary**

- **Available? No.** Google has confirmed this on their own issue tracker: ["Mediapipe datasets aren't public"](https://github.com/google-ai-edge/mediapipe/issues/3727).
- What we know from the [paper](https://arxiv.org/abs/2006.10214):
  - ~**30,000 real-world images** with manually annotated 21 keypoints in image coordinates.
  - A **synthetic dataset** rendered from a high-quality 3D hand model across 24 poses, multiple lighting conditions and camera angles, providing ground-truth 2.5D coordinates.
  - Training mixed both: real for image domain coverage, synthetic for depth supervision.
- For anyone wanting to retrain or extend, Google's official path is **[MediaPipe Model Maker](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer)**: you bring labeled gesture images, the existing landmark model runs over them to extract 21 keypoints, and you train a small classifier on top of those landmarks. You never retrain the landmarker itself.

### Papers

- **Primary paper:** Zhang, Bazarevsky, Vakunov, Tkachenka, Sung, Chang, Grundmann. *"MediaPipe Hands: On-device Real-time Hand Tracking."* CVPR 2020 Workshop on Computer Vision for Augmented and Virtual Reality. [arXiv:2006.10214](https://arxiv.org/abs/2006.10214).
- **Companion engineering write-up:** ["On-Device, Real-Time Hand Tracking with MediaPipe"](https://research.google/blog/on-device-real-time-hand-tracking-with-mediapipe/), Google Research blog, August 2019.
- **Framework paper (parent):** Lugaresi et al., *"MediaPipe: A Framework for Building Perception Pipelines"*, [arXiv:1906.08172](https://arxiv.org/abs/1906.08172).

### What this means for `Hand_AI`

We get rich geometry for free (21 points × 3D × handedness), at the cost of zero ability to retrain the upstream model. Everything we do — pinch, point, fist, open_palm — is **geometry on top of those 21 points**, which is exactly why our [`assets/js/gestures.js`](https://github.com/warrenrross/Hand_AI/blob/main/assets/js/gestures.js) is small, deterministic, and tunable rather than learned. The trade-off is the one Warren spent two photo rounds diagnosing: foreshortening artifacts in the 2D projection that the landmarker is happy to hand us, which our heuristics have to reason about (see v2.1 `indexDominance` and v2.2 `POINT_DOMINANCE=1.6`).

---

## 4. Six follow-on threads that built on this work

Ordered roughly by ambition / scale.

### 4.1 HaGRID + HaGRIDv2 — Hand Gesture Recognition Image Dataset

- Repo: [hukenovs/hagrid](https://github.com/hukenovs/hagrid). Paper: [arXiv:2206.08219](https://arxiv.org/html/2206.08219v2).
- **What it adds over EgoHands:** EgoHands gave you 4,800 first-person images of generic "hand". HaGRIDv2 gives you **1,086,158 FullHD images across 33 distinct gesture classes plus a `no_gesture` class**, in COCO bounding-box format, totaling 1.5 TB.
- **Why it matters here:** this is the modern public successor to EgoHands. Anyone trying to do *gesture* classification (not just hand detection) now starts here. Google's [official gesture recognizer customization guide](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer) explicitly trains on HaGRID-style data.

### 4.2 Google's MediaPipe Gesture Recognizer (canned classifier)

- Docs: [Gesture Recognizer Task](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer). Source: [mediapipe/tasks/python/vision/gesture_recognizer.py](https://github.com/google/mediapipe/blob/master/mediapipe/tasks/python/vision/gesture_recognizer.py).
- **What it adds:** ships a pre-trained 7-class classifier on top of the same HandLandmarker — `Closed_Fist`, `Open_Palm`, `Pointing_Up`, `Thumb_Down`, `Thumb_Up`, `Victory`, `ILoveYou`. Plus Model Maker for adding custom classes.
- **Why it matters here:** this is the "if we got tired of writing heuristics" exit path. Our gesture vocabulary (fist / pinch / point / open_palm / thumbs_up) overlaps five of these seven by name. We could swap our [`classifyGesture`](https://github.com/warrenrross/Hand_AI/blob/main/assets/js/gestures.js) for the canned recognizer and lose: pinch (not in the set, would need custom training) and our explicit white-space states (`near_pinch`, `curling`).

### 4.3 kinivi/hand-gesture-recognition-mediapipe — MLP-on-landmarks reference

- Repo: [kinivi/hand-gesture-recognition-mediapipe](https://github.com/kinivi/hand-gesture-recognition-mediapipe) (fork-translation of [Kazuhito00's original](https://github.com/Kazuhito00/hand-gesture-recognition-mediapipe), the same repo we already cite in [`gestures.js`](https://github.com/warrenrross/Hand_AI/blob/main/assets/js/gestures.js)).
- **What it adds:** trains a tiny MLP on the 21 normalized landmarks to classify static signs, and a second model on the time series of fingertip motion for dynamic gestures. Starter classes: open / close / pointing.
- **Why it matters here:** this is the pattern Warren could adopt if heuristics stop scaling. The architecture is *exactly* what we'd build next — same input (21 keypoints from MediaPipe), small learned classifier, browser-friendly. It's the bridge between v2.2's hand-tuned thresholds and a future v3 that learns the boundaries from labeled data.

### 4.4 ASL fingerspelling via MediaPipe Model Maker

- Write-up: [Sam Pröll, "Customizing a gesture recognition model with MediaPipe"](https://samproell.io/posts/ai/asl-detector-with-mediapipe-wsl/) (April 2024).
- **What it adds:** end-to-end recipe — collect images per letter, run Model Maker, get a deployable TFLite model that plugs back into the standard Tasks Vision API. Reports >95% accuracy on ASL alphabet with a few hundred samples per class.
- **Why it matters here:** demonstrates that the "21 landmarks → small classifier" approach works in practice for novel vocabularies, not just for the seven canned gestures. If we ever want Hand_AI to recognize, say, a "scissor" or "rock" gesture without hand-coding it, this is the cheapest path.

### 4.5 FingerNet — registerable gesture recognition on MediaPipe landmarks (2024)

- Paper: Meng, Jiang, Duan, Wen. *"Real-Time Hand Gesture Monitoring Model Based on MediaPipe's Registerable System."* Sensors 24(19):6262, September 27 2024. [DOI 10.3390/s24196262](https://doi.org/10.3390/s24196262) — [PMC11478756](https://pmc.ncbi.nlm.nih.gov/articles/PMC11478756/).
- **What it adds:** trains a small ResNet variant ("FingerNet") on top of the 21 MediaPipe landmarks to produce a 32-dimensional gesture embedding. New gestures are added by **registering** a few examples and storing the cluster centroid — no retraining required. Borrows the FaceNet trick ([Schroff et al. 2015](https://arxiv.org/abs/1503.03832)) of triple-loss metric learning. Includes a custom **FingerComb** block: parallel 1D convolutions with kernels 1×2 / 1×3 / 1×4 along a finger-structured `1 × 22 × 3` input, so the network learns adjacent-joint, three-joint, and whole-finger patterns simultaneously.
- **Static, not temporal.** Single hand, single frame (`max_num_hands=1`). Does not use MediaPipe Holistic, does not use an LSTM. The authors call out weak performance on two-handed and complex motion gestures as an explicit limitation.
- **Accuracy:** 0.878 on their own private 1,600-sample dataset (RGDS), 0.953 on public AUTSL (Turkish Sign Language) where six other methods beat them, 0.572 on ChaLearn IsoGD (narrow win in a generally low-scoring field).
- **Dataset availability:** **not public** — *"Data is unavailable due to privacy restrictions."* All 1,600 samples were sourced from the paper's authors themselves. AUTSL ([cvml.ankara.edu.tr](https://cvml.ankara.edu.tr/), [paper](https://arxiv.org/abs/2008.00932), 38,336 videos / 226 signs / 43 signers) and ChaLearn IsoGD are public if anyone wants to reproduce.
- **Code availability:** no GitHub link in the paper; I could find no public reference implementation.
- **Training:** PyTorch 1.13, RTX 8000, 500 epochs, batch 256, LR 0.2, triple loss + cross-entropy. Train/test split is by **class** (28 train / 4 held-out for registration testing) — the correct way to validate a registerable system.
- **Why it matters here:** points at a different upgrade path than the temporal one I had originally framed. The registerable pattern matches Hand_AI's actual use case — Warren defines a small gesture vocabulary, may want to add new ones over time, and would rather not retrain a closed-set classifier each time. Static embedding + nearest-centroid is also simpler than an LSTM and stays compatible with the existing per-frame MediaPipe pipeline. Limitation we'd inherit: a single-subject dataset of 50 samples per gesture won't generalize across hand shapes or lighting without expansion.
- **Real-world deployment surface (not demonstrated in the paper, but enabled by the method):** custom shortcut palettes that users enroll themselves, accessibility/AAC vocabularies tuned per user, sign-language teaching tools that grade student attempts by embedding distance, procedure-specific gesture sets in clinical/industrial training.
- **Successors / forks of this paper specifically:** none I could find — paper is 14 months old, *Sensors* venue, no code release, private data. For the *adjacent* temporal-LSTM lineage that I originally mistook this for, see §4.6 below.

### 4.6 MediaPipe + LSTM for continuous gesture and sign-language recognition

A separate, broader thread of work — landmarks as a stable feature extractor under recurrent temporal models. This is the direction the `AGENT_NOTES.md` roadmap item "temporal smoothing of dominance/curl ratios" actually points at.

- **Starting point — community tutorial:** [nicknochnack/ActionDetectionforSignLanguage](https://github.com/nicknochnack/ActionDetectionforSignLanguage) (June 2021) and its [YouTube walkthrough](https://www.youtube.com/watch?v=doDUihpj6ro). TensorFlow/Keras, MediaPipe Holistic (543 landmarks per frame), stacked LSTM over 30-frame sequences. Most of the academic work below is essentially this pattern, formalized.
- **Peer-reviewed hand-only version:** [Biswas et al., 2023 (CVIP)](https://dspace.nitrkl.ac.in/dspace/bitstream/2080/4092/1/2023_CVIP_SBiswas_MediaPipe.pdf) — "MediaPipe with LSTM Architecture for Real-Time Hand Gesture Recognition," 98.99% on a custom 26-class dataset. Hand landmarks only, no holistic. Closest stack to where Hand_AI lives today.
- **Most recent journal version:** [MP-GestLSTM (2025)](https://www.tandfonline.com/doi/full/10.1080/21642583.2025.2587853) — Taylor & Francis, December 2025. MediaPipe + LSTM real-time gesture detection.
- **Sign-language ASL (arXiv 2025):** [SLRNet, Khan et al.](https://arxiv.org/pdf/2506.11154.pdf) — uses all 543 MediaPipe Holistic landmarks, stacked LSTM over 30-frame sequences, 26 ASL alphabet letters + 10 functional words ("help," "sleep," "sorry"), 86.7% validation accuracy on a custom dataset.
- **Sign-language ISL:** [Rao et al., 2025 (IJCA)](https://ijcaonline.org/archives/volume187/number25/ravikiran-2025-ijca-925415.pdf) — Indian Sign Language, 6 gestures, 99.4% on dynamic. And [the EAI Transactions paper, 2025](https://publications.eai.eu/index.php/airo/article/view/8693) — ISL, Sequential LSTM + MediaPipe Holistic, 11 gestures, 96.97% accuracy.
- **Public datasets used in this lineage:** AUTSL ([cvml.ankara.edu.tr](https://cvml.ankara.edu.tr/)), [RWTH-PHOENIX-Weather 2014T](https://www-i6.informatik.rwth-aachen.de/~koller/RWTH-PHOENIX-2014-T/) (39 GB, German sign language, continuous), CSL-Daily (Chinese sign language).
- **Production caveat worth flagging:** a [recent r/MachineLearning thread](https://www.reddit.com/r/MachineLearning/comments/1pepjtf/r_machine_learning_model_algorithm_for_sign/) from a developer trying to scale this approach to 150 ASL signs on mobile reports that MediaPipe landmarks become unreliable under varying lighting, camera quality, and occlusion — to the point that they recommend ingesting raw pixels alongside landmarks rather than landmark sequences alone. Matches the failure mode we already hit twice in the v2.1 / v2.2 photo grill rounds. Any future learned model for Hand_AI should plausibly take both.

---

## 5. Honorable mention — the academic parent everyone built on

- **OpenPose** ([CMU-Perceptual-Computing-Lab/openpose](https://github.com/CMU-Perceptual-Computing-Lab/openpose)) and the **CMU Panoptic Hand Database** ([domedb.perception.cs.cmu.edu/handdb](http://domedb.perception.cs.cmu.edu/handdb.html)).
- Paper: Simon, Joo, Matthews, Sheikh. *"Hand Keypoint Detection in Single Images using Multiview Bootstrapping."* CVPR 2017. ([arXiv](https://arxiv.org/abs/1704.07809))
- Datasets are public: 1,912 manually-annotated training hands, 14,261 synthetic, 14,817 multiview-bootstrapped. Total ~31K — the same order of magnitude Google cites for MediaPipe's real-image set.
- Not used directly by either of Warren's projects, but it's the methodological ancestor: the multiview-bootstrapping idea (use a labeled subset to bootstrap labels on unlabeled views, retrain) is widely understood to be how Google generated their unreleased corpus at scale.

---

## 6. Resources actually grabbable today

Distilled from §2–§5. What's reachable if we decide to retrain or fine-tune anything.

### 6.1 Datasets available for hand pose / gesture training

| # | Dataset | Size | Labels | Source |
|---|---|---|---|---|
| 1 | **EgoHands** (Bambach et al., ICCV 2015) | 4,800 images, >15K hand instances, 48 first-person videos | Pixel-level segmentation masks + 4-class hand identity (myleft / myright / yourleft / yourright) | [vision.soic.indiana.edu/egohands](http://vision.soic.indiana.edu/egohands/) · COCO-format mirror on [Roboflow](https://public.roboflow.com/object-detection/hands) |
| 2 | **HaGRIDv2** (Hukenov et al., 2022→2024) | 1,086,158 FullHD images, 1.5 TB | 33 gesture classes + `no_gesture`, COCO-format bounding boxes | [github.com/hukenovs/hagrid](https://github.com/hukenovs/hagrid) · [arXiv:2206.08219](https://arxiv.org/html/2206.08219v2) |
| 3 | **CMU Panoptic Hand DB** (Simon et al., CVPR 2017) | ~31K hands total — 1,912 manual + 14,261 synthetic + 14,817 multiview-bootstrapped | 21 hand keypoints (same skeleton MediaPipe uses) | [domedb.perception.cs.cmu.edu/handdb.html](http://domedb.perception.cs.cmu.edu/handdb.html) |
| 4 | **AUTSL** (Sincan & Keles, 2020) | 38,336 video samples | 226 Turkish Sign Language signs, 43 signers, RGB + depth | [cvml.ankara.edu.tr](https://cvml.ankara.edu.tr/) · [arXiv:2008.00932](https://arxiv.org/abs/2008.00932) |
| 5 | **RWTH-PHOENIX-Weather 2014T** (Koller et al., RWTH Aachen) | 39 GB, 386 weather forecasts (2009–2011) | Continuous German Sign Language with gloss + spoken-language translation | [www-i6.informatik.rwth-aachen.de/~koller/RWTH-PHOENIX-2014-T](https://www-i6.informatik.rwth-aachen.de/~koller/RWTH-PHOENIX-2014-T/) |
| 6 | **ChaLearn LAP IsoGD** | ~48K RGB-D videos | 249 isolated gesture classes | ChaLearn LAP challenge — referenced in Meng et al. benchmarks; current download link not personally verified |
| 7 | **MediaPipe Model Maker RPS sample** | Small starter set (rock / paper / scissors / none) | 4 gesture classes via folder-name labeling | [storage.googleapis.com/mediapipe-tasks/gesture_recognizer/rps_data_sample.zip](https://storage.googleapis.com/mediapipe-tasks/gesture_recognizer/rps_data_sample.zip) |

**Not available** (flagged so we don't go hunting):
- MediaPipe Hands training data — Google confirmed *"Mediapipe datasets aren't public"* on [issue #3727](https://github.com/google-ai-edge/mediapipe/issues/3727)
- Meng et al. 2024 RGDS — *"Data is unavailable due to privacy restrictions"*
- All the LSTM-paper custom datasets (Biswas 2023, SLRNet 2025, the two ISL papers) — collected per-paper, not released

### 6.2 Pretrained, open-weight models suitable for transfer learning

| # | Model | What it gives you | Transfer-learning surface | Source |
|---|---|---|---|---|
| 1 | **MediaPipe HandLandmarker** | 21 3D keypoints per hand, two-stage palm-detect + landmark regression, real-time on-device | Use as **frozen feature extractor**. Cannot be retrained (proprietary data), but its landmark output is the standard input for everything below. | [ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) |
| 2 | **MediaPipe Gesture Recognizer** | 7 canned gestures (Closed_Fist, Open_Palm, Pointing_Up, Thumb_Down, Thumb_Up, Victory, ILoveYou) | **Model Maker** lets you fine-tune the classifier head on landmark-extracted images of your own classes. Whole landmark backbone stays frozen. | [ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer) |
| 3 | **Handtrack.js / Dibia handtracking model** | Bounding-box hand detection, browser-deployable via TensorFlow.js | SSD + MobileNetV1 checkpoint trained on EgoHands. Standard TF Object Detection API retraining flow. Apache 2.0 license. | [github.com/victordibia/handtracking](https://github.com/victordibia/handtracking) · [github.com/victordibia/handtrack.js](https://github.com/victordibia/handtrack.js/) |
| 4 | **OpenPose hand model** (Simon et al., CMU) | 21-keypoint hand detection with confidence maps | Trained weights downloadable; full architecture and training script open. **Non-commercial license** — worth noting. | [github.com/CMU-Perceptual-Computing-Lab/openpose](https://github.com/CMU-Perceptual-Computing-Lab/openpose) |
| 5 | **kinivi / Kazuhito00 MLP-on-landmarks** | Tiny MLP classifier sitting on top of MediaPipe landmarks; static-sign + dynamic-fingertip motion variants | Reference implementation with included `keypoint_classifier.tflite`. Drop-in retrain on your own landmark CSVs — the cleanest "build your own classifier head" starting point. | [github.com/kinivi/hand-gesture-recognition-mediapipe](https://github.com/kinivi/hand-gesture-recognition-mediapipe) · [github.com/Kazuhito00/hand-gesture-recognition-mediapipe](https://github.com/Kazuhito00/hand-gesture-recognition-mediapipe) |
| 6 | **MobileNetV1 / V2 ImageNet checkpoints** | General-purpose image classification backbones; what Dibia transfer-learned from for Handtrack.js | Standard transfer-learning starting point for any hand bounding-box model. Available in TensorFlow Hub, TFJS, PyTorch torchvision. | TensorFlow Hub · torchvision |

**Worth flagging:**
- **No open-weight successor to MediaPipe HandLandmarker exists yet.** Everything in the open-source ecosystem treats it as a frozen feature extractor and trains heads on top. If we want to retrain end-to-end, OpenPose's hand model is the only public 21-keypoint model with both weights and training pipeline available.
- **The FingerNet model from §4.5 is not in this table** — no released weights, no code repo. Architecture is documented but we'd be reimplementing from scratch.
- **The LSTM models from §4.6 are not in this table** — each paper trained on its own private custom dataset, no released weights. The nicknochnack tutorial repo gives the *architecture* (stacked LSTM on MediaPipe Holistic) but not pretrained weights.

---

## 7. Open questions / TBD for Warren

- **Two distinct upgrade paths are now on the table, and they're not the same:**
  - *Static, per-frame:* swap heuristics for either Google's canned Gesture Recognizer (§4.2) or a registerable embedding model in the FingerNet style (§4.5). Cheaper, fits Hand_AI's current per-frame architecture, lets users enroll their own gestures. Starter pretrained surface: MediaPipe Gesture Recognizer + Model Maker (§6.2 row 2) or kinivi/Kazuhito00 MLP-on-landmarks (§6.2 row 5).
  - *Temporal, motion-aware:* adopt the MediaPipe + LSTM family (§4.6) to recognize *motions* (push-to-spawn, swipe-to-dismiss) rather than poses. Heavier; requires buffering frame sequences; opens the door to dynamic gestures the current architecture can't express. No pretrained weights available — we'd train from scratch on our own data.
- Do we want to capture our own labeled gesture dataset (a few hundred examples per class on Warren's phone, palm-down and palm-side) as a future option for switching to a learned classifier? Same dataset works for either upgrade path above. HaGRIDv2 (§6.1 row 2) is the obvious public dataset to either augment with or pretrain against first.
- Worth re-evaluating the canned MediaPipe Gesture Recognizer (§4.2) head-to-head against our v2.2 heuristics on the same 12 photos from the v2.1/v2.2 grill rounds? Cheap experiment, would clarify whether we're reinventing or outperforming.
- The roadmap item "wire thumbs_up to action" overlaps directly with Gesture Recognizer's `Thumb_Up` class — if we ever bring in the canned model, that wiring comes for free.
- The Reddit caveat in §4.6 (landmarks degrade on mobile cameras under poor lighting) is the same failure mode we already hit twice in our photo rounds. Any future learned model probably needs to ingest raw pixels alongside landmarks rather than landmarks alone.

---

## 8. Custom dataset capture — concept and components

The long-running question behind this repo: **should Warren build software to gather a custom hand-gesture dataset?** The §6 grabbable resources are all useful but none are a perfect fit for the Hand_AI use case — webcam/phone selfies under uncontrolled lighting, with the gesture vocabulary Warren actually wants. A custom capture tool is plausible if (a) no existing dataset covers the gap and (b) no off-the-shelf labeling tool already does this. Both appear to be true.

The initial concept (from Warren, May 2026): a **mobile-friendly web app backed by a VPS** that makes it easy for volunteers to contribute labeled hand images.

Research has surfaced three viable data sources that are best treated as **cooperating layers**, not as alternatives:

1. **Synthetic CGI rendering** — MANO/NIMBLE rigs + Blender + domain randomization. Free perfect labels at scale. The CVPR 2025 [HandSynthesis](https://github.com/delaprada/HandSynthesis) paper shows synthetic-only training can reach **84–97%** of real-data accuracy.
2. **Mobile-web volunteer capture** — phone-camera selfies, auto-labeled with MediaPipe HandLandmarker. Real-world artifacts, real demographic variation, real consent and moderation questions.
3. **Low-grade Gaussian splats** — 30-second phone-video orbits of held poses. Turns one volunteer-minute into thousands of re-rendered labeled views. Aspirational but possibly within reach.

The rest of the work is split into topic-scoped supplemental docs in [`docs/`](./docs/) — see the index below. RESEARCH.md remains the lineage/state-of-the-art anchor; the docs go deep on the dataset-capture tooling decision.

### Sub-topic index (`docs/`)

| Doc | Scope | Key questions answered |
|---|---|---|
| [`docs/dataset-architecture.md`](./docs/dataset-architecture.md) | The three-layer side-by-side framing | How do synthetic, mobile capture, and splats divide labor? What's the v1 architecture? What fails gracefully? |
| [`docs/synthetic-rendering.md`](./docs/synthetic-rendering.md) | MANO/NIMBLE/DART/HandSynthesis pipelines | What synthetic tools exist? What's the sim-to-real gap actually made of? What do the ablations say to prioritize? |
| [`docs/gaussian-splats.md`](./docs/gaussian-splats.md) | Low-grade splats for hand assets | Can a phone video produce a usable hand splat today? Static vs. articulating. Polycam/Luma vs. research lineage (GauHuman → HandSplat → GraG). |
| [`docs/mobile-capture-pipeline.md`](./docs/mobile-capture-pipeline.md) | Web app + VPS architecture | Why mobile-camera capture specifically? Auto-labeling strategy. What the VPS actually does. |
| [`docs/open-questions.md`](./docs/open-questions.md) | Consent, licensing, scope, sequencing | Biometric data legality. MANO/NIMBLE license math. v1 scope. What we don't know yet. |
| [`docs/roadmap.md`](./docs/roadmap.md) | Starting-point roadmap (synthetic-first → personal hyperpersonalization) | Phase 0 cheap experiment, Phase 1 synthetic baseline beating v2.2, Phase 2 ship Hand_AI v3, Phase 3 per-player splat capture for personalization. |
| [`docs/architecture-classification-vs-localization.md`](./docs/architecture-classification-vs-localization.md) | How the pipeline separates *what gesture* from *where on screen*; what each candidate classifier (heuristics, canned, Model Maker, Phase 1 synthetic) does and doesn't change. | Does retraining the classifier improve targeting? (No — targeting is HandLandmarker coordinates, upstream of every classifier.) |
| [`docs/experiments/phase0-gesture-recognizer.md`](./docs/experiments/phase0-gesture-recognizer.md) | Phase 0 experiment record — canned MediaPipe Gesture Recognizer on the 12 v2.2 grill-round photos | Did the canned model beat heuristics? (Result: 0/12; mixed signal, see writeup for caveats and decision.) Reproducible bundle in [`tests/phase0-gesture-recognizer/`](./tests/phase0-gesture-recognizer/). |
| [`docs/experiments/phase0b-model-maker-paths.md`](./docs/experiments/phase0b-model-maker-paths.md) | Phase 0b plan — two paths to retrain the classifier head via MediaPipe Model Maker: real photos + in-game test (Path A) vs. synthetic renders + held-out evaluation (Path B). | What does Model Maker actually require? What's the cheapest way to test it? When is the synthetic path worth the infrastructure? |
| [`docs/experiments/phase0c-hand-ai-fork-roadmap.md`](./docs/experiments/phase0c-hand-ai-fork-roadmap.md) | Phase 0c plan — fork Hand_AI, add a parallel `GestureRecognizer` pipeline alongside the existing `HandLandmarker`, deploy via GitHub Pages, A/B-test in-game with a `?classifier=heuristics\|learned\|both` query param. Required before any in-game Model Maker test is possible. | What integration work does Hand_AI actually need? How does the fork → original PR flow work? What's the bar to promote fork changes to the live site? |

### How this connects back

- The motivation for any of this traces to **§4.6** (the Reddit thread observing MediaPipe landmarks degrade on mobile cameras) and **§7** (open question about capturing our own labeled gesture data).
- The output of this work — if it goes anywhere — feeds either of the §7 upgrade paths: static per-frame classifier (kinivi/Kazuhito00-style MLP head, or Google Gesture Recognizer via Model Maker) or temporal LSTM (§4.6 family). The dataset is the same either way.
- Existing public datasets we'd compete with or augment are catalogued in **§6.1**; pretrained models we'd train on top of are in **§6.2**.

---

*Sources cited inline. Companion to [AGENT_NOTES.md](https://github.com/warrenrross/Hand_AI/blob/main/AGENT_NOTES.md) (engineering decisions + threshold provenance) and [README.md](https://github.com/warrenrross/Hand_AI/blob/main/README.md) (gesture vocabulary + roadmap). Sections: 1. Lineage · 2. thehandtrick · 3. Hand_AI · 4. Follow-on threads · 5. Academic parent (OpenPose / CMU Panoptic) · 6. Grabbable resources · 7. Open questions · 8. Custom dataset capture (→ [docs/](./docs/)).*
