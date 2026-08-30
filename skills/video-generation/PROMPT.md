# Standalone video-generation prompt

Copy everything in the code block below into a fresh agent (claude.ai, another
Claude Code session, or any capable coding agent), fill in the two bracketed
lines, and send it. It encodes the same code-drawn method this skill uses, so
the agent won't wander off toward video editors or AI footage.

```
Build an animated motion-graphics video using Remotion (the React-based video
framework — remotion.dev). Draw everything in code: text, shapes, gradients,
and motion are React/TypeScript components animated with Remotion's
useCurrentFrame(), spring(), and interpolate(), using SVG and CSS. Do NOT use
AI text-to-video (Sora/Veo), stock footage, a screen recorder, or a video
editor — build the visuals programmatically.

Set up a standard Remotion project:
- package.json deps: remotion, @remotion/cli, react, react-dom (+ typescript,
  @types/react as dev deps). Scripts: "studio": "remotion studio",
  "render": "remotion render Video out/video.mp4".
- src/index.ts calls registerRoot(Root).
- src/Root.tsx defines a <Composition id="Video"> at 1920x1080, 30fps.
- A master component stitches scenes together with <Sequence from=... durationInFrames=...>.
- Put each scene in its own file under src/scenes/, and keep brand colors and
  fonts in a shared src/theme.ts so the whole look can be re-skinned in one place.
- Use Remotion's random(seed) — never Math.random()/Date.now() — so renders are
  deterministic.

Workflow: build the scenes, then verify a few frames as stills with
`npx remotion still Video out/frame.png --frame=N` (open the PNG to check it)
BEFORE rendering the full video with `npx remotion render Video out/video.mp4`.
Confirm the MP4 exists at the end and report its path, length, and resolution.
The video is silent unless you add a soundtrack via Remotion's <Audio> component.

For a vertical/social cut, register a second <Composition id="VideoVertical">
at 1080x1920 reusing the same scenes, and render that id.

SUBJECT / BRIEF: [describe the brand or topic, the scenes/message you want, any
brand colors, the length, and whether you want landscape, vertical, or both]
DELIVERABLE: [e.g. a 15-second 1920x1080 MP4, silent, energetic neon look]
```

## Tips for filling it in

- **Be concrete about the subject.** "A 15s promo for a cold-brew coffee brand
  called Nightshift, dark palette with amber accents, three feature callouts
  (Smooth, Strong, Cold), ending on 'Coming this fall'." beats "a coffee video".
- **State the length and format** — the agent will pick pacing from it.
- **Name real brand colors** if they exist; otherwise say the mood (neon,
  pastel, corporate, retro) and let the agent choose.
- **Mention audio explicitly** if you want it — otherwise expect a silent video.
