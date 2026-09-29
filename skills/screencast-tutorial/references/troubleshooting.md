# Troubleshooting

Ordered by how often each one bites. The SKILL.md table covers the quick cases;
this is for when it is not enough.

## Diagnose before changing anything

```bash
# 1. What does the app actually look like right now?
npx ts-node src/inspect.ts --routes "/,/the-route" --audience admin

# 2. Does the script's own path work?
npx ts-node src/pipeline.ts --validate --script the-script

# 3. Watch one take happen
PLAYWRIGHT_HEADLESS=false npx ts-node src/pipeline.ts --record-only --script the-script
```

Step 3 is the one people skip. Most "the pipeline is broken" reports are one
stale selector, and watching the take shows which one immediately.

Also read the two artifacts from any failed run:

- `output/raw/<script>/page@*-timings.json` — the measured segment boundaries.
  If `narrationStartMs - startMs` is huge, the action phase stalled. If
  `endMs - narrationStartMs` is far below the narration duration, the hold
  aborted.
- The gate/action failure list printed during recording, which names the
  selector that caused each failure.

## "readySelector not visible after 30s"

In order of likelihood:

1. **The selector drifted.** A rename, an id change, a copy change. Re-run the
   inspector. Do not guess the replacement.
2. **The page needs an interaction first.** The selector lives inside a modal or
   a tab panel that is not open yet. Add the `click` action *before* the
   navigation, or point the segment's `readySelector` at something that exists
   on the landing page and use the modal selector in a later segment.
3. **The route is wrong.** A redirect landed somewhere else. The inspector
   reports the final `url`, which is the reliable answer.
4. **The app is genuinely slow.** Raise `readyTimeoutMs` in config. If the app
   is slow *only on cold load*, add the caching asset proxy (see architecture
   reference) rather than inflating timeouts everywhere.

## "Login failed" or a video that is just the login page

Login is asserted (URL must leave `/login`), so this is a real failure, not a
silent one.

```bash
# Does the credential work at all?
npx ts-node src/inspect.ts --routes "/" --audience admin
```

- **UI login fails, credentials look right** — the app may need a CSRF token
  obtained from a prior GET, or a tenant/slug step before the form renders.
  Drive that step in the inspector, then encode it in `uiLogin.loginPath`.
- **Token mint returns 401** — almost always the identifier field name. Backends
  read `email`, `identifier`, or `username`. Confirm against the login
  controller.
- **Token mint returns 429/too many** — throttle. Wait out the window, and
  switch that audience to `localStorage-token` so the next batch costs one
  login instead of N.
- **Injected token yields no shell** — handled automatically (falls back to UI
  login), but if it recurs the token is probably scoped wrong. Check that
  `tokenKey` matches where the SPA actually reads from, and that any tenant
  metadata the app needs is in `localStorage.seed`.

## Footage is slow-motion, or audio drifts from video

The audio-first invariant is broken. Narration must exist *before* recording.

```bash
npx ts-node src/pipeline.ts --audio-only --script the-script   # ensure audio exists
npx ts-node src/pipeline.ts --record-only --script the-script  # re-record
npx ts-node src/pipeline.ts --merge-only --script the-script   # re-merge
```

If the freeze-pad warning appears in the merge log, the recorded window came up
short. That is a symptom, not the disease: the hold was not long enough, which
usually means narration was regenerated with different text after recording. If
it appears on a healthy take, raise `TAIL_MS` in `merge.ts`.

## A segment is a frozen frame

The hold outran the narration and nothing moved.

- The segment's only actions were `navigate`/`wait`, which are stripped before
  the "has visible actions" check. The recorder auto-scrolls in that case, so a
  frozen frame means the scroll ran and the page had nothing to scroll (content
  shorter than the viewport). Add a `scroll` action that has somewhere to go, or
  add a real interaction.
- If the segment does change something, the recorder holds static on purpose.
  That is correct; the fix is more on-screen motion during the narration, not a
  shorter narrator.

## `__name is not defined`

A bundler injected a `__name` helper into arrow functions passed to
`page.evaluate`. When Playwright serializes the function to run in the page, the
helper does not exist there.

Fixes, in order:

1. Use `ts-node` (as the pipeline ships). tsx and esbuild enable `keepNames` by
   default and trip this.
2. Use `$$eval` with a regular `function` expression, or `locator` APIs, instead
   of `page.evaluate`.
3. Pass data as an argument rather than closing over outer variables:
   `page.evaluate((arg) => {...}, arg)`.

`inspect.ts` is written to avoid the pattern entirely.

## TTS: `Stream closed` / `WebSocket` errors

The Edge TTS websocket drops mid-stream fairly often, especially on bursts of
back-to-back synthesis. Handled automatically: up to `TTS_MAX_RETRIES` (default
4) attempts with a fresh client and linear backoff.

- **Persistent failures** — the service is rate-limiting. Add a delay between
  segments in `ensureAudio()`, or reduce concurrency to one process.
- **Silent corruption** — a tiny buffer is treated as a drop and the cache entry
  is discarded, so a truncated mp3 never reads as "cached". If a segment's
  narration sounds cut off, delete `output/audio/<script>__<segment>.mp3` and
  re-synthesize.
- **Zero duration reported** — ffprobe could not read the file, so the segment
  is treated as missing audio and recording refuses to proceed rather than
  producing a silent segment.

## Pages hang loading assets

Symptom: navigation succeeds (`waitUntil: 'commit'` returns on first bytes) but
content never paints; spinners never clear; readySelectors time out.

Usually server-side HTTP/2 stream exhaustion. Chromium opens many parallel
streams for lazy chunks; some servers drop them after the first few.

Fix: add the caching asset proxy described in the architecture reference. It
intercepts asset requests, fetches them over Node's HTTP/1.1, and caches to
disk. First load is slow, later takes are fast. It is the single highest-leverage
fix for a slow target app, and better than raising every timeout.

## Only some scripts fail

Sort by what differs between them.

- **Specific routes fail** — those pages are slower, heavier, or gated. Compare
  their `shellTimeoutMs` need against the passing ones.
- **Everything after the first few fails** — resource exhaustion, not selectors.
  Multiple Chromium instances or a leaked proxy will do this. Check for orphaned
  browser processes between runs; the recorder closes its browser, but a crashed
  run may not.
- **Same script fails only sometimes** — flaky selector or a race in the app.
  Re-run to confirm, then look for a `wait` that is too short. Prefer waiting on
  a selector over waiting on a duration.

## The merge produces a file that will not play

- **Zero bytes or a truncated file** — a segment ffmpeg pass failed, or the
  concat filelist referenced a missing file. Re-run `--merge-only`; the segments
  on disk are still valid.
- **Codec/parameter mismatch between segments** — should not happen since every
  segment goes through the same filter chain, but a hand-edited segment can
  break it. Re-run `--merge-only` to normalize.
- **Audio/video drift accumulates across segments** — the cut is landing on the
  wrong frame. Confirm `-c:v copy` is not in use anywhere in the filter chain;
  stream-copying VFR webm is the cause.

## Before concluding it is fixed

Watch a final video at 1x, not just the pipeline log. The gate log says the
selector was visible; only playback shows whether the narration matched the
screen. A green run and a wrong video are both possible states, and only one of
them is a real deliverable.
