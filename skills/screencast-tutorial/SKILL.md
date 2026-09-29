---
name: screencast-tutorial
description: "Record narrated screen-walkthrough tutorials of any web app. Use when asked to make tutorial videos, product walkthroughs, onboarding demos, feature explainers, or 'a video showing how to use X'. Drives the real app in a browser with Playwright, narrates each step with free neural TTS, merges audio+video with FFmpeg, and can publish to YouTube. Also use to fix an existing screencast batch: narration that runs ahead of the UI, slow-motion footage, desync, black-segment takes, or selectors that stopped matching."
---

# Screencast tutorial pipeline

Record narrated, screen-synced walkthroughs of a real web app. Every video is
authored as a JSON script (narration + browser actions per segment), validated
against the live app, then captured and merged.

**This is not a video editor or a motion-graphics tool.** It films software. If
the ask is animation, marketing montage, or a composed visual, hand off to
`video-generation` (Remotion), `hyperframes` (HTML video), or
`faceless-explainer` (no product UI to film).

## What it is actually for

The hard part of a screen walkthrough is sync: the speaker must describe the
screen the viewer is looking at, not the screen they were looking at three
clicks ago. Every design decision below exists to make that structural rather
than a matter of luck.

The five rules, in order of how much damage breaking them causes:

1. **Audio before video.** Synthesize narration first. Exact durations are then
   known when the recorder sizes each hold. Generate audio *after* recording and
   you are guessing, which forces time-stretching and slow-motion desync.
2. **Narration describes the settled screen.** Every segment names a
   `readySelector`. The narrator starts only once that element is visible, so
   the speaker can never outrun the UI.
3. **Never time-stretch.** The recorder holds for narration + tail, so the cut
   is always exactly lead + narration long and video plays at native speed. A
   clip that comes up short is freeze-padded, never slowed.
4. **Assert success, never assume it.** A failed login that leaves the page on
   the form used to produce a confident video of the login screen. Login, settle
   gates, and every action are checked and reported.
5. **Select observed, not remembered.** Author scripts from inspector output.
   Guessed selectors are the single largest source of failed takes.

## When to use

- "Make a tutorial video for the dashboard", "record a walkthrough of onboarding"
- "Add a product demo video", "video showing how to configure X"
- Re-recording a batch after a UI rename broke the selectors
- Diagnosing a screencast: audio ahead of visuals, slow-motion, frozen segments

## Don't use for

| Ask | Use instead |
|---|---|
| Animated/motion-graphics video, promo reel | `video-generation`, `hyperframes` |
| Faceless explainer, no product UI to film | `faceless-explainer` |
| Editing an existing video, adding captions | `embedded-captions`, `talking-head-recut` |
| Live browser QA against a running app | `webapp-testing`, `gstack-qa` |

## Workflow

Copy the pipeline into the target project, then work these phases. Phases 1-3
are config and authoring; the expensive part is phase 5, so do not reach it
until validation is green.

```bash
# 0. Install the pipeline into the target project
cp -r <skill>/assets/pipeline <target-repo>/tools/screencast
cd <target-repo>/tools/screencast
npm install && npx playwright install chromium
cp config/app.config.example.json config/app.config.json   # then edit
cp .env.example .env                                      # then fill in
```

Requirements: Node 18+, FFmpeg + ffprobe on PATH, and a reachable environment
with valid test credentials. TTS needs no API key and no Python.

### 1. Inspect the target app — never skip

```bash
npx ts-node src/inspect.ts --discover --routes "/,/settings,/reports" --audience admin
```

Logs in, expands collapsed nav, and dumps headings, buttons, inputs, links,
tabs, comboboxes, dialogs, and empty states per route to
`output/ui-inspection.json`. This output is the source of truth for every
selector in phase 3. Skipping it is the main reason takes fail.

### 2. Configure audiences

`config/app.config.json` holds every app-specific fact: base URLs, auth
strategy, login selectors, which selectors mean "still loading", and the
shutdown/warm-up route. One pipeline serves many apps and many user roles —
add an entry under `audiences` per role rather than forking code. See
[references/configuration.md](references/configuration.md).

Prefer `localStorage-token` auth when the app has an API: mint one bearer token
per batch instead of logging in per video, which avoids login throttles (many
APIs cap ~5 attempts / 15 min per credential+IP) that a re-record loop trips
immediately. `ui-login` is the fallback and is required for videos that show the
login screen itself.

### 3. Author scripts

One JSON file per video under `scripts/`. One idea per segment, narration 15-25s
describing the settled screen. Full schema in
[references/script-schema.md](references/script-schema.md); start from
`scripts/example-dashboard-tour.json`.

Prefer selectors in this order: **id / data-testid > aria-label > role+text >
placeholder > CSS class**. Text and class selectors break on copy changes;
ids and testids are usually there precisely so tests and tooling can rely on
them. If the app lacks stable hooks, that is an app bug worth reporting, not a
reason to pin a script to a class name.

### 4. Validate before recording

```bash
npx ts-node src/pipeline.ts --validate               # all scripts
npx ts-node src/pipeline.ts --validate --script x    # one
```

Walks every route, action, and `readySelector` against the live app with no
recording. Green means the take will not stall mid-segment. Fix every failure
here; a failed selector discovered after a 3-minute take costs 3 minutes.

### 5. Record

```bash
npx ts-node src/pipeline.ts --script x     # one: audio -> record -> merge
npx ts-node src/pipeline.ts --all          # every script
```

Stages are individually runnable (`--audio-only`, `--record-only`,
`--merge-only`) so a failed merge never costs a re-record. Narration mp3s are
cached, so re-recording is fast and TTS cost is paid once.

Review `output/final/*.mp4` at 1x before publishing. Watch for: narration
landing before the described UI, a segment's scroll not moving, and frozen
frames (a sign the hold outran the narration).

### 6. Publish

```bash
npx ts-node src/pipeline.ts --auth-youtube   # one-time OAuth
npx ts-node src/pipeline.ts --upload         # resumable, idempotent
```

## Recovering from failures

| Symptom | Cause | Fix |
|---|---|---|
| Footage is slow-motion | Audio generated after recording | Regenerate audio first (`--audio-only`), then re-record |
| Narration describes the wrong screen | `readySelector` wrong or too broad | Re-inspect the route, tighten the selector |
| Segment is a frozen frame | Hold outran the narration | Shorten the narrator text; verify TTS duration |
| `readySelector not visible after 30s` | Selector drifted, or route needs different navigation | Re-inspect; check whether the page needs a click first |
| Video shorter than narration | Cut came up short | Harmless; `tpad` freeze-pads and logs a warning |
| Login page recorded as content | Login silently failed | Now asserted; if it recurs, check credentials in `.env` |
| `__name is not defined` | `page.evaluate` arrow fn under a `keepNames` bundler | Use `$$eval` or `ts-node` (as shipped) |
| TTS `Stream closed` | Edge websocket dropped | Automatic retry; raise `TTS_MAX_RETRIES` if persistent |
| HTTP/2 assets hang | Server-side stream exhaustion | Raise `readyTimeoutMs`, or add a caching asset proxy (see architecture ref) |
| Login throttled mid-batch | Too many UI logins | Switch that audience to `localStorage-token` |

## Reference material

Load these only when the phase you are in needs them.

| Doc | Read it when |
|---|---|
| [references/configuration.md](references/configuration.md) | Setting up a new app or a new user role |
| [references/script-schema.md](references/script-schema.md) | Authoring or debugging scripts |
| [references/architecture.md](references/architecture.md) | Understanding sync, hold math, or the merge model; extending the pipeline |
| [references/troubleshooting.md](references/troubleshooting.md) | A take failed and the table above is not enough |
| [references/lessons-learned.md](references/lessons-learned.md) | Understanding why a rule exists before changing it |
