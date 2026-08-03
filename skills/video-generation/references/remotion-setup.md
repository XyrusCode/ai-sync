# Remotion setup & commands

Everything you need to scaffold, preview, verify, and render. Read this before
the first render.

## Project anatomy

The `assets/template/` folder is a ready-to-run project. Its structure:

```
<project>/
├── package.json            deps + scripts (render targets the composition id)
├── tsconfig.json           ES2020 / ESNext / jsx: react-jsx
├── remotion.config.ts      jpeg frames, overwriteOutput
├── src/
│   ├── index.ts            registerRoot(Root)  ← entry point
│   ├── Root.tsx            <Composition> definitions (Video + VideoVertical)
│   ├── config.ts           FPS, WIDTH/HEIGHT, scene end-frames, duration
│   ├── theme.ts            COLORS + fonts  ← customize FIRST per subject
│   ├── Video.tsx           master: stitches scenes with <Sequence> + Flash
│   └── scenes/
│       ├── TitleScene.tsx    opening title/logo build (+ particles)
│       ├── ContentScene.tsx  main message / staggered callouts
│       └── OutroScene.tsx    end card / call-to-action
└── out/                    render output (created on first render)
```

The load chain: `index.ts` → `registerRoot(Root)` → `Root.tsx` `<Composition>`
→ `Video.tsx` → `scenes/*`. A composition's `id` (e.g. `Video`) is what you pass
to render/still commands.

## Scaffold a new project

```bash
# from the folder where the project should live
cp -r "<skill>/assets/template" ./my-video      # or copy in your shell of choice
cd my-video
# set the package name (edit package.json "name": "my-video")
npm install                                       # ~30-60s first time
```

On Windows PowerShell, `Copy-Item "<skill>\assets\template\*" .\my-video -Recurse`.

## The commands

| Command | What it does |
| --- | --- |
| `npm run studio` | Opens **Remotion Studio** in a browser — timeline, scrubbing, hot reload. Best for hands-on tweaking. |
| `npx remotion compositions` | Lists composition ids in the project. Use if a render "not found" error appears. |
| `npx remotion still Video out/frame.png --frame=60` | Renders **one frame** to a PNG. Fast. Do this to verify before a full render. |
| `npx remotion render Video out/video.mp4` | Renders the whole `Video` composition to MP4 (h264). |
| `npx remotion render VideoVertical out/vertical.mp4` | Renders the 9:16 composition. |

Add `--frames=0-60` to `render` to produce a short clip while iterating.

## The verify loop (do this — it saves time)

1. Change a scene or `theme.ts`.
2. `npx remotion still Video out/check.png --frame=<a frame inside that scene>`.
3. **Read the PNG.** Fix layout/color/timing issues now, while feedback is
   one frame away instead of a multi-minute full render.
4. Repeat for one frame per scene (e.g. frames 45, 150, 300).
5. Only then run the full `render`.

To choose frames: a scene spanning frames `A`–`B` (see `src/config.ts`) is best
sampled near its middle, once its entrance animation has settled.

## Composition size & length

Set in `src/config.ts`:
- `FPS` (30 is a good default; 60 for very smooth motion at larger file size).
- `WIDTH`/`HEIGHT` (1920×1080 landscape; the vertical comp uses 1080×1920).
- Scene end-frames (`TITLE_END`, `CONTENT_END`, `OUTRO_END`) and
  `DURATION_IN_FRAMES`. Seconds = frames ÷ FPS.

## Common errors

- **"No composition with the id … found"** — the id passed to render doesn't
  match `Root.tsx`. Run `npx remotion compositions` to see the real ids.
- **Blank/black frame** — usually a scene threw; check the still, and that the
  frame you sampled is within a scene's `<Sequence>` range.
- **Font looks wrong** — the named font isn't available headless. Load it
  explicitly (see the fonts note in `SKILL.md`).
- **Slow render** — lower `FPS`, reduce particle counts, or render a frame
  range while iterating. Concurrency auto-scales to CPU cores.
