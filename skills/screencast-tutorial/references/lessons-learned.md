# Lessons learned

Each of these came from a failed batch. They are here so the rules in SKILL.md
are not mistaken for arbitrary style preferences.

## Generate audio before recording, not after

The original pipeline recorded first, then synthesized narration, then
time-stretched the footage to fit. Every video came out in visible slow motion
and the narration drifted against the UI.

Reversing the order fixed it structurally: exact narration durations are known
before recording, so each hold is sized to fit and the merge never stretches.
**Never let a change reintroduce a post-recording audio step**, even for a
single "quick re-record"; that is exactly the case that tempts you.

## The narrator must describe the settled screen

Early scripts said things like "Now click Reports" and "Choose the term
dropdown". By the time those played, the click had already happened and the
dropdown was open. The viewer heard the speaker describing a screen that had
already been left behind.

Fix: every segment names a `readySelector`, and narration starts only once it is
visible. Script authors had to rewrite narrations to describe state rather than
intent. It felt slower and produced markedly better videos.

## Assert that login worked

Login errors were caught, logged to nothing, and swallowed. The recorder
captured whatever was on screen, which after a silently failed login was the
login form. The output was a confident, well-narrated tutorial of the wrong
thing.

Now login retries and throws. A failed take is better than a plausible wrong
video, and the failure is visible instead of shipping.

## Never time-stretch; freeze-pad instead

When a clip came up short, the instinct was to slow it to fit. Slow motion is
readable as "broken" and breaks comprehension across the whole segment. Freezing
the last frame is a one-frame artifact the viewer barely notices.

The asymmetry is the point: jank is local, desync is global.

## Re-encode cuts, never stream-copy

`-c:v copy` on the per-segment cuts is much faster and looked fine in spot
checks. But the source is variable-frame-rate webm, and stream copy drifts
against the wall-clock timings, so cuts land on the wrong frame. The drift is
small per segment and accumulates visibly across a video.

Re-encoding costs merge time and buys cuts that land where the timings say.

## Observe selectors, never remember them

Scripts written from a reading of the source, or from memory of a previous
version, broke on every copy change. Running the inspector first and authoring
from its output eliminated a whole class of failed takes.

This is why `inspect.ts` ships with the pipeline rather than being a one-off
utility. The step is the fix.

## Mint one token per batch, not one per video

Login throttles are typically per credential and IP over a time window. A
sixteen-video batch, and any re-record loop, exhausts that in the first few
videos. Every subsequent video then recorded a login page, which the silent
failure mode turned into plausible-looking output.

One cached token per audience turns N logins into one. The UI login path stays
as a fallback for when the token is stale or the contract is unknown.

## Pre-suppress the product tour

An onboarding overlay auto-opened on first load, dimmed the page, and swallowed
clicks on early segments. Actions silently failed while the video looked fine.

It is a localStorage flag with no server-side counterpart, so the only fix is to
plant it before the app boots. `localStorage.seed` exists for exactly this class
of first-visit interference. Expect to find one of these in any new app.

## Cap the silent lead-in

The action phase (before narration starts) is capped at `MAX_LEAD_MS`. A slow
config gate could stretch it to 40 seconds, and the segment would open on
dead loading time. The transition is worth showing; the wait is not.

## Use a wall-clock deadline for auto-scroll

With `slowMo` enabled, each synthetic wheel event costs ~300ms, so counting
steps overshoots the narration length badly — the segment ends with the page
scrolled somewhere meaningless. A wall-clock deadline cannot overshoot.

## Check the final video, not just the pipeline log

A green run means the selectors matched and the gates passed. It does not mean
the narration matched the screen. Only watching a final video at 1x catches the
difference between a working pipeline and a working deliverable.

The gate log is necessary and insufficient.

## What would be worth building next

Not built, and honestly not needed yet. Listed so the tradeoff is a decision
rather than an oversight.

- **Caching asset proxy.** The single highest-leverage fix for slow target apps.
  Only worth adding when a specific app needs it, because it is real code with
  real failure modes.
- **Per-segment re-record.** Would help long scripts, at the cost of the
  continuous timeline that makes cuts frame-accurate.
- **Alternative TTS providers.** `msedge-tts` is free and keyless, so swapping
  costs only a replacement for `synthesizeToFile()`.
