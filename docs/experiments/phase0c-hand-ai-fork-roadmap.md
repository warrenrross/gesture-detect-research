# Phase 0c — Hand_AI fork with GestureRecognizer integration

> **Parent:** [`docs/roadmap.md` — Phase 0](../roadmap.md#phase-0--decide-whether-to-build-any-of-this-blocking)
> **Predecessors:** [`phase0-gesture-recognizer.md`](./phase0-gesture-recognizer.md) · [`phase0b-model-maker-paths.md`](./phase0b-model-maker-paths.md)
> **Architecture reference:** [`docs/architecture-classification-vs-localization.md`](../architecture-classification-vs-localization.md)
> **Status:** Planned. Roadmap drafted 2026-05-21; execution scheduled for the next session.

## Why this exists

[Phase 0b's Path A](./phase0b-model-maker-paths.md) initially proposed "drop the trained model into Hand_AI and play." Inspection of the current [Hand_AI codebase](https://github.com/warrenrross/Hand_AI) showed that's not actually possible as-described: [`assets/js/handTracker.js`](https://github.com/warrenrross/Hand_AI/blob/master/assets/js/handTracker.js) loads MediaPipe's `HandLandmarker` (landmarks only), and gesture classification happens entirely in [`assets/js/gestures.js`](https://github.com/warrenrross/Hand_AI/blob/master/assets/js/gestures.js) as v2.2 heuristics on those landmarks. There is no classifier head in the running game to swap.

To run any in-game test of a learned classifier — canned, Model Maker, or Phase 1 synthetic — Hand_AI needs a parallel `GestureRecognizer` pipeline added alongside (not replacing) the existing `HandLandmarker` path. This doc roadmaps that work.

## What needs to change in Hand_AI

Three real changes, all in the fork (not the original yet):

### 1. Add `GestureRecognizer` to `handTracker.js`

The [@mediapipe/tasks-vision](https://www.npmjs.com/package/@mediapipe/tasks-vision) module already imported by `handTracker.js` exposes `GestureRecognizer` alongside `HandLandmarker`. Same WASM runtime, same CDN, no new dependency.

New init pattern (sketch):

```js
const GESTURE_MODEL_URL =
  new URLSearchParams(location.search).get("gestureModel") ||
  "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task";

const { HandLandmarker, GestureRecognizer, FilesetResolver } = mod;
const fileset = await FilesetResolver.forVisionTasks(WASM_BASE);

// Existing landmarker — unchanged.
this.landmarker = await HandLandmarker.createFromOptions(fileset, { /* same as today */ });

// New: parallel gesture recognizer.
this.recognizer = await GestureRecognizer.createFromOptions(fileset, {
  baseOptions: { modelAssetPath: GESTURE_MODEL_URL, delegate: "GPU" },
  runningMode: "VIDEO",
  numHands: 1,
});
```

Per-frame call gets a second invocation:

```js
detect(video, nowMs) {
  // Monotonic-timestamp guard (existing).
  let t = Math.floor(nowMs);
  if (t <= this._lastTimestamp) t = this._lastTimestamp + 1;
  this._lastTimestamp = t;

  const landmarks = this.landmarker.detectForVideo(video, t)?.landmarks || [];
  const gestureResult = this.recognizer.recognizeForVideo(video, t);
  const learnedLabel = gestureResult?.gestures?.[0]?.[0] || null;

  return { landmarks, learnedLabel };
}
```

The change is additive — the existing landmark consumers don't have to know about the second pipeline.

### 2. Make the model URL configurable

A URL query param (`?gestureModel=<url>`) is the cheapest way to swap between the canned `gesture_recognizer.task` and a future Model-Maker-trained `.task` without rebuilding. Default to the canned model.

This becomes critical at Phase 0d (training a custom head). For tomorrow's first pass, the canned URL is fine.

### 3. Add a classifier A/B flag in `app.js`

A second query param decides which classifier drives the game event:

| `?classifier=` | Behavior |
|---|---|
| `heuristics` (default) | Current v2.2 path. Backwards-compatible default — nothing changes for the live site. |
| `learned` | Use the `GestureRecognizer` label only. v2.2 disabled. |
| `both` | Both pipelines run; HUD displays both labels side-by-side; game event still fires from v2.2 (safe). |

`both` mode is the most useful for grill rounds — you see in real time when the learned head agrees or disagrees with v2.2, without changing game behavior.

This is the **only honest way** to compare them in the same play session: same webcam, same lighting, same gestures, same frame. Anything else is comparing memories of two play sessions.

## Deployment via GitHub Pages

GitHub Pages works on forks. The setup:

1. Fork `warrenrross/Hand_AI` (default branch: `master`).
2. Push the changes to a feature branch.
3. Settings → Pages → enable on the feature branch (or merge to fork's `master` and enable there).
4. Live URL: `https://warrenrross.github.io/<fork-name>/`.

The original `https://warrenrross.github.io/Hand_AI/` is unaffected. You can play both side-by-side in two browser tabs.

**CORS:** Canned MediaPipe models are served from `storage.googleapis.com` with permissive CORS — same as today. A future custom `.task` from Model Maker needs CORS-friendly hosting; GitHub raw via `cdn.jsdelivr.net` works (`https://cdn.jsdelivr.net/gh/<user>/<repo>@<branch>/<path>`). Decision for later.

## Tomorrow's execution plan (in order)

Branch: `phase0c-gesture-recognizer` on a Hand_AI fork. Default branch `master` (Hand_AI convention).

| Step | Action | Verification |
|---|---|---|
| 1 | Fork `warrenrross/Hand_AI` to a new repo (suggested name: `Hand_AI-gesture-recognizer-experiment`). | Fork visible under `warrenrross/` on GitHub. |
| 2 | Branch `phase0c-gesture-recognizer` off `master` in the fork. | `git branch --show-current` returns expected name. |
| 3 | Modify `assets/js/handTracker.js`: add `GestureRecognizer` init + per-frame call. Return `{ landmarks, learnedLabel }` from `detect()`. | Manually load the fork's `index.html` locally; confirm browser console shows both pipelines initializing. |
| 4 | Update `assets/js/app.js`: read `?classifier=` query param; route gesture-event source accordingly; in `both` mode, render both labels in the HUD. | Open `?classifier=heuristics` → behaves identically to live site. Open `?classifier=learned` → uses canned labels only. Open `?classifier=both` → HUD shows both. |
| 5 | Light QA on the existing v2.2 path. The change must be strictly additive — no regression on default behavior. | Side-by-side with live `warrenrross.github.io/Hand_AI/` shows identical gesture firing on same poses. |
| 6 | Push the branch. Enable GitHub Pages on the fork pointing at the branch. | Get a working `https://warrenrross.github.io/<fork-name>/` URL. |
| 7 | Warren plays the fork with `?classifier=both`. Reports back with screenshots + verdict on whether the canned labels agree with v2.2 on real in-game poses. | Verdict captured in a new experiment record `docs/experiments/phase0c-gesture-recognizer-ingame.md` in this research repo. |

**Estimated effort:** Steps 1–6 are ~1–2 hours of focused work for Computer. Step 7 is whatever play time Warren wants to spend, but a useful first pass is 5–10 minutes per `?classifier=` mode.

## Branching strategy across repos

Three repos touched. Standing rules (from session context):

| Repo | Default branch | Role |
|---|---|---|
| `warrenrross/Hand_AI` | `master` | Original live game. Untouched until Phase 0c proves itself. |
| `warrenrross/Hand_AI-gesture-recognizer-experiment` (planned fork) | `master` | Experiment surface. Pages-deployed. Fast iteration. |
| `warrenrross/gesture-detect-research` | `main` | Research record. Phase 0c writeup lives here. Original Hand_AI gets a one-line note pointing at the fork. |

## What lands where, when

### Tomorrow's session (Phase 0c integration)

- **In `Hand_AI-gesture-recognizer-experiment` fork:** the changes from Steps 3–4 above, on branch `phase0c-gesture-recognizer`, merged to fork's `master` once verified. Pages live.
- **In `gesture-detect-research`:** a new file `docs/experiments/phase0c-gesture-recognizer-ingame.md` recording the in-game test results (Warren's screenshots + verdict). Cross-links updated.
- **In `Hand_AI` (original):** a one-line note in `AGENT_NOTES.md` pointing at the fork and the research-repo writeup. **No code changes** to the original yet.

### A later session (only if Phase 0c justifies it)

- **In `Hand_AI` (original):** open a PR from the fork's `phase0c-gesture-recognizer` branch into `warrenrross/Hand_AI:master`. This is the polished version of the A/B harness shipped to the live site. v2.2 stays the default; learned-classifier mode is opt-in via the query param. This PR ships separately from any specific trained model.
- **In `gesture-detect-research`:** writeup of the live-site rollout decision.

### Phase 0d (Model Maker training) — also a later session

- Warren captures real photos per class.
- Computer trains via Model Maker, exports `gesture_recognizer.task`.
- Hosts the file on jsdelivr-via-GitHub-raw.
- Updates the fork's default `gestureModel` URL or adds a third `?classifier=trained` mode.
- Warren plays. Writeup in research repo.

## Decision rule for "promote fork changes to original Hand_AI"

The fork is the experiment surface; the original is the production site. Bar to merge fork → original:

- The A/B harness has been exercised in `?classifier=both` mode for at least one play session.
- v2.2 default behavior is verified unchanged.
- The code is clean enough to live in the original repo's style (it's a buildless static site; no new dependencies should land).
- Warren has tested all three `?classifier=` modes and confirmed they do what they say.

If any of those fails, the changes stay in the fork until they pass.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| `GestureRecognizer` and `HandLandmarker` running in parallel doubles per-frame cost; could hurt frame rate. | `both` mode is opt-in only via query param. Default behavior unchanged. If FPS suffers, can serialize the two calls or fall back to running `GestureRecognizer` at half the rate. |
| Monotonic-timestamp invariant for VIDEO mode applies to *both* pipelines independently. | Maintain separate `_lastTimestamp` for each, or pass the same `t` to both — MediaPipe handles same-frame calls fine as long as `t` is non-decreasing per pipeline. |
| Fork drifts from upstream Hand_AI over time. | Phase 0c branch is short-lived; if it lives more than a couple of sessions, rebase against upstream `master` before each new round of work. |
| Page CORS issues if a custom `.task` URL is added later. | Use jsdelivr-via-GitHub-raw: `https://cdn.jsdelivr.net/gh/warrenrross/<repo>@<branch>/<path>`. Tested working with MediaPipe in the past. |
| Warren plays the fork without realizing the original site is still on v2.2 — confusion about which URL is which. | The HUD in fork shows the active `?classifier=` mode prominently. The original `Hand_AI/` site is documented as the v2.2 baseline. |

## Open questions for tomorrow

- Should the fork name be `Hand_AI-gesture-recognizer-experiment` (descriptive) or something shorter like `Hand_AI-fork`? Descriptive seems better since this might not be the only experimental fork.
- For `?classifier=both` mode, should the HUD show the learned label inline with v2.2's gesture, or in a separate diagnostic panel? Probably inline for first pass.
- Does `gesture_recognizer.task` from Google's CDN need `minHandPresenceConfidence` set, or does it use its own internal defaults? Check before the first run.

## Pointers

- [`phase0-gesture-recognizer.md`](./phase0-gesture-recognizer.md) — the original sandbox experiment that motivated all of this.
- [`phase0b-model-maker-paths.md`](./phase0b-model-maker-paths.md) — the two training paths; Phase 0c is the integration work that makes Path A even possible.
- [`docs/architecture-classification-vs-localization.md`](../architecture-classification-vs-localization.md) — why this only touches the classifier head, not targeting.
- [Hand_AI/assets/js/handTracker.js](https://github.com/warrenrross/Hand_AI/blob/master/assets/js/handTracker.js) — the file Phase 0c modifies.
- [MediaPipe Gesture Recognizer task page](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer) — official API + 8-label vocabulary.
- [@mediapipe/tasks-vision on npm](https://www.npmjs.com/package/@mediapipe/tasks-vision) — the module exposing both `HandLandmarker` and `GestureRecognizer`.
