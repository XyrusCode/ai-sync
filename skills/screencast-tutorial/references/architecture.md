# Architecture

Why the pipeline is shaped this way, and what to preserve when changing it.

## The desync problem

The first version of this pipeline generated audio *after* recording. That forces
two bad options, and both were bad:

- **Record on a fixed guess** (4s per segment) then stretch footage to fit
  narration. Result: slow-motion video, and the speaker visibly out of sync.
- **Record long, then cut.** Result: still needs the cut to land on the exact
  narration boundary, which drifts on variable-frame-rate webm.

The fix inverts the order. Synthesize narration first, measure it with ffprobe,
then size every hold from the real duration. The recorded window is then always
at least as long as lead-in plus narration, and the merge never has to stretch
anything.

## Three stages

```
1. audio   narration mp3 per segment          cheap, cached, no browser
2. record  one continuous webm + timings JSON  expensive, gated
3. merge   cut, mix, concat -> mp4             cheap, ffmpeg only
```

Stages are separately runnable (`--audio-only`, `--record-only`, `--merge-only`)
so a merge bug never costs a re-record. Narration mp3s are cached on disk, so
re-recording is fast and TTS is paid once per segment, ever.

## Timings: three instants per segment

Recording produces one continuous webm for the whole script. To cut it, the
recorder measures wall-clock offsets from the moment the page (and video
capture) was created:

| Field | Meaning |
|---|---|
| `startMs` | The clip starts. On-camera action phase begins. |
| `narrationStartMs` | The described UI has painted. **Narration begins here.** |
| `endMs` | The clip ends. |

The gap between `startMs` and `narrationStartMs` is the action phase: the
viewer watches the click happen *before* the speaker explains it. That ordering
is what makes the video feel like it is keeping up with the viewer.

`startEpoch` is captured immediately after `newPage()`, before login and
warm-up. Measuring from after login would shift every cut earlier by the login
duration and desync the whole video.

## Hold math

```
TAIL_MS     = 1200     // hold after narration ends
MIN_HOLD_MS = 3500     // floor for very short segments
holdMs = max(narrationMs + TAIL_MS + holdAfterMs, MIN_HOLD_MS)
```

The floor matters for a different reason than it looks: a segment with a
500ms narration still needs enough window for the viewer's eye to travel to the
described element.

## Settle gates

`waitForSettled()` blocks until the page is genuinely ready, in three stages:

1. **Shell mounted** — `shell.readyRootSelector` attached.
2. **Spinners gone** — nothing in `shell.spinnerSelectors` visible.
3. **Content ready** — the segment's `readySelector` visible, or (when absent)
   shell text stable across two reads ~800ms apart.

Gates 1 and 2 are app-level; gate 3 is per-segment. All return a list of
failures rather than throwing, so the caller decides: log and continue (default,
so one bad segment does not cost the whole take) or abort under
`STRICT_GATES=true`.

**Never weaken a gate to make a take pass.** A gate failure is a real signal
that the page was not ready, and the video would show narration over the wrong
screen. Fix the selector or the navigation instead.

The text-stability fallback exists because a sidebar often renders before the
content panel. A body-text gate passes on a shell-only page. Measure text
*inside* the shell root and require stability, not just presence.

## Merge: ratio locked to 1.0

Per segment:

```
leadMs   = min(narrationStartMs - startMs, MAX_LEAD_MS)   // 2500 default
cutMs    = [narrationStartMs - leadMs .. min(endMs, narrationStartMs + narrationMs + TAIL_MS)]
targetMs = leadMs + narrationMs + TAIL_MS
padMs    = max(0, targetMs - cutMs)
```

One ffmpeg pass per segment:

```
-ss/-to (window)  -i video  -i audio
-filter_complex
  "[0:v]tpad=stop_mode=clone:stop_duration=padSec,fps=30,format=yuv420p[v];
   [1:a]adelay=leadMs:all=1,apad,loudnorm=I=-16:TP=-1.5:LRA=11[a]"
-t targetSec -c:v libx264 -crf 23 -c:a aac -b:a 128k
```

Four decisions worth preserving:

- **`tpad=stop_mode=clone`** — a short clip freezes its last frame rather than
  being slowed. Visible jank beats slow-motion desync, because jank is a
  one-frame artifact and desync ruins comprehension.
- **`adelay`** — narration trails the action by `leadMs` of silence. Without it
  the speaker runs ahead of the click.
- **Re-encode, never `-c:v copy`.** VFR webm plus stream copy drifts; segment
  boundaries would land off the wall-clock timings. This is why the merge is
  slower than a naive concat and why the ratio is trustworthy.
- **`loudnorm`** — TTS output and any captured audio land at a predictable
  level across all segments.

Finally, `ffmpeg -f concat` over the per-segment files. The filelist is deleted
after; a stale filelist silently re-merges old segments.

## Auth: one token per batch, not per video

Many backends throttle login hard (commonly 5 attempts / 15 min per
credential+IP). A 16-video batch, or a single re-record loop, blows through
that immediately and then produces videos of a login page.

So: mint one bearer token through the app's own API, cache it in
`output/tokens.json` (12h TTL), and seed localStorage via `context.addInitScript`
before the SPA boots. The recorder also verifies the result — an injected token
that yields no app shell is treated as stale, dropped, and replaced with a real
UI login.

**Login is asserted, never assumed.** Success means the URL left `/login`.
Previously errors were swallowed and a frozen login page was recorded as a
successful tutorial.

## Extensions to consider

Things deliberately left out because no target app needed them. If one does:

**Caching asset proxy.** Some servers (notably Apache with certain HTTP/2
configurations) exhaust streams after the first few, so a cold page load hangs
on JS chunks. Fix: intercept `**/assets/**` in the context, fetch via Node
HTTP/1.1, cache to disk by path, and serve from cache on later runs. This turns
a 20s-per-chunk cold load into a sub-second one after the first take. Add to
`createSession()` in `record.ts`.

**Per-segment re-record.** Currently a take is all-or-nothing per script. For
long scripts, record each segment as its own webm so a failed segment re-records
alone. The cost is losing the single continuous timeline that makes cuts
frame-accurate, so it is a real tradeoff, not a free win.

**Multiple TTS providers.** `msedge-tts` is free and keyless, which is why it is
the default. Swapping in a paid provider means replacing `synthesizeToFile()`;
nothing else in the pipeline cares where the mp3 came from.
