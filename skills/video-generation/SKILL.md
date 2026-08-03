---
name: video-generation
version: 1.0.0
description: >-
  Generate animated videos with Remotion — motion graphics drawn entirely in
  code (React/TypeScript) and rendered to a real MP4. Use whenever the user
  wants to create, make, or produce a video, promo, advert, animation, motion
  graphics, intro/outro, explainer, product demo, trailer, or short-form/social
  clip (Reels, TikTok, Shorts) — for a brand, a local code project, or any
  subject they name — even if they never say "Remotion". This is the default
  way to make a video here. Do NOT reach for AI text-to-video (Sora/Veo), stock
  footage, screen-recording tools, or a video editor unless the user explicitly
  asks for one; build it in code instead.
requires:
  bins: ["node"]
---

# Video Generation (Remotion)

Make videos by writing them as code. Every visual — text, shapes, gradients,
motion — is a React component drawn frame-by-frame and rendered to MP4 by
[Remotion](https://remotion.dev). No editor, no stock footage, no AI-generated
frames. This is deterministic, versionable, and re-renderable: change a color or
a word, run one command, get a new video.

## Why this framing matters

A generic "make a video" request sends most agents toward tools they can't run
(video editors) or can't produce reliably (text-to-video models). That is the
#1 failure mode. **Everything here is CSS/SVG/React animated with math.** Hold
that line unless the user explicitly wants real footage or AI video.

The machine is already set up: Node 22, and Remotion's headless Chrome shell is
downloaded from prior renders. `npm install` in a new project is all that's
needed.

## Pick the mode

Read the one reference file for the mode that fits, then follow the core
workflow below. Modes combine freely (e.g. a promo, then a social cut of it).

| The user wants… | Mode | Read |
| --- | --- | --- |
| A brand/product promo, advert, logo intro, kinetic-typography spot | **Motion graphics** | `references/motion-graphics.md` |
| To showcase one of their local apps (yt-grab, ani-jelly-pipeline, …) | **Code-project demo** | `references/project-demos.md` |
| To explain a concept/topic, animate data or charts, teach something | **Explainer / data** | `references/explainer-data.md` |
| A vertical 9:16 cut, captions, or a short-form edit of any of the above | **Social cut** | `references/social-cuts.md` |
| Music or sound effects on any of the above | **Audio** (add-on) | `references/audio.md` |

If unsure which mode, ask the user one short question about the goal and
audience — but if they've given enough (a subject + a vibe), just pick and go.

## Core workflow

Full command details and the project anatomy are in
`references/remotion-setup.md` — read it before the first render. In short:

1. **Scaffold.** Copy this skill's `assets/template/` into a new project folder
   (default under the current project, e.g. `./<name>-video/`, or ask). Set the
   `name` in `package.json`. Run `npm install`.
2. **Make it about the subject.** This is the real work:
   - Edit `src/theme.ts` — swap `COLORS` for the subject/brand palette and fonts.
   - Edit the scenes in `src/scenes/` — replace the `TODO: subject` copy
     (`TitleScene`, `ContentScene`, `OutroScene`) with real headlines, points,
     and a call to action. Add or remove scenes as the story needs.
   - Adjust pacing in `src/config.ts` (scene end-frames, total duration).
3. **Verify a still first.** `npx remotion still Video out/frame.png --frame=N`
   for a few representative frames, and **Read the PNG** to confirm it looks
   right. This is far faster than rendering the whole video to catch mistakes.
4. **Render.** `npx remotion render Video out/video.mp4`. For the vertical cut,
   render the `VideoVertical` composition (see `references/social-cuts.md`).
5. **Confirm and report.** Check `out/*.mp4` exists and state the path, length,
   resolution, and whether it has audio.

For live iteration the user can run `npm run studio` (opens Remotion Studio in a
browser with a timeline and hot reload) — good to suggest for hands-on tweaking.

## Checklist & gotchas

- **The render id must match a composition id.** `remotion render Video …`
  renders the `<Composition id="Video">` in `src/Root.tsx`. Rename in both or
  neither. Listing compositions: `npx remotion compositions`.
- **Still-before-render, always.** Rendering hundreds of frames to discover a
  typo wastes minutes. One `remotion still` and a Read catches most issues.
- **Fonts.** System fonts render fine. For a specific brand font, load it via
  `@remotion/google-fonts` or a local file — don't assume an arbitrary font
  name resolves in the headless browser.
- **Determinism.** Never use `Date.now()`/`Math.random()` in components — they
  make renders non-reproducible and flicker. Use Remotion's `random(seed)` and
  `useCurrentFrame()` instead (the template already does).
- **Silent by default.** Renders have no audio unless you wire it up — see
  `references/audio.md`. When reporting the result, say whether it has sound.
- **Windows/PowerShell.** Commands here are shell-agnostic; `npx remotion …`
  works the same. Output lands in `out/`.

## Worked example

A complete real project built this way lives at
`C:\Users\Xyrus\Desktop\XyrusCode\tasks\stylex-promo\` (the "Stylex" energy-drink
promo). It's the fuller, hand-tuned version of this template — read its
`src/scenes/*` for richer animation ideas (liquid waves, a drawn product can,
sheen sweeps).

## Standalone prompt

`PROMPT.md` holds a self-contained prompt that encodes this same method for use
in a context without this skill (Codex.ai, a fresh non-Codex agent).
Offer it to the user when they want to drive a video build elsewhere.
