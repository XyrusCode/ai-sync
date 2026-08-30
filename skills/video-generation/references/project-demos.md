# Mode: Code-project demos

Showcase one of the user's local apps (yt-grab, ani-jelly-pipeline,
x-feed-replacer, xyrus-youtube-plucker, etc.). Two approaches — pick by whether
real footage of the app is wanted.

## Approach A — Scripted UI walkthrough (default, pure Remotion)

Recreate the app's flow as motion graphics: stylized UI panels, a moving cursor,
text typing in, results appearing. Fully code-drawn, so it's clean, deterministic,
and needs nothing running. Best for a polished "here's what it does" promo.

Build it like a motion-graphics piece (`motion-graphics.md`) but with
app-specific scenes:
- **Hook scene** — app name + one-line value prop ("yt-grab — download any
  YouTube video, natively").
- **Flow scenes** — one per step. Draw a rounded "window" (an `AbsoluteFill`
  with a title bar), then animate the interaction:
  - **Typing** — reveal a string by slicing it to `Math.floor(frame * charsPerFrame)`.
  - **Cursor** — a small div moved with `interpolate`/`spring` to the button,
    then a click pulse (quick scale-down/up + a ripple ring).
  - **Progress** — a bar whose width is an `interpolate` of frame; a spinner via
    `rotate(${frame * k}deg)`.
  - **Result** — the output card springs in.
- **Outro** — repo/name + call to action (stars, try it, install command).

Pull real specifics from the project (actual button labels, the real CLI
command, true feature names) by reading its README/source — accuracy makes the
demo credible. For yt-grab it's a Tauri v2 desktop app; reflect that framing.

Mock the UI in the brand's spirit; you don't need a pixel-perfect clone, just a
recognizable, tasteful representation of the real flow.

## Approach B — Record the real running app

Only when the user wants genuine footage of the actual app. Remotion animates
graphics, not your screen, so recording is a separate capture step, then you can
optionally composite it into a Remotion project (titles, zooms, captions).

- **Capture:** use the OS/tooling the user has (e.g. an installed screen
  recorder, OBS, or `ffmpeg` if present) to record the app to an `.mp4`/`.webm`.
  Ask the user to record it, or drive the app if a browser/automation tool is
  available for a web UI. Do not assume a recorder exists — confirm first.
- **Composite (optional):** drop the capture into `public/` and place it in a
  Remotion scene with `<OffthreadVideo src={staticFile('demo.mp4')} />`, then
  overlay animated titles, highlight boxes, zoom (animate `scale`/`translate`),
  and captions. This yields a produced demo rather than a raw screen grab.
- **Browser apps:** if the project is web-based and a browser automation tool is
  connected, you can navigate the running dev server and capture frames; still
  composite/annotate in Remotion.

## Choosing

- Want it fast, clean, and evergreen (no re-record when the UI changes) →
  Approach A.
- Want to prove "this really runs" or show real output data → Approach B, ideally
  composited so it still looks produced.
