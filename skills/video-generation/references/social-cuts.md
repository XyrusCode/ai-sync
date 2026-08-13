# Mode: Social cuts (vertical / short-form / captions)

Reformat any of the other modes for Reels, TikTok, and Shorts: vertical 9:16,
optional captions, tighter edits. The template already ships a second
composition for this.

## Vertical 9:16

`src/Root.tsx` registers **`VideoVertical`** at 1080×1920 reusing the same
`<Video>` content. Render it with:

```bash
npx remotion render VideoVertical out/vertical.mp4
```

Because the scenes are centered with `AbsoluteFill` + flex centering, most
content re-centers automatically. But **verify with a still** —
`npx remotion still VideoVertical out/v.png --frame=60` — and fix:
- **Overflow** — big headlines that fit 1920 wide will wrap at 1080. Reduce
  `fontSize`, allow wrapping, or shorten copy for the vertical cut.
- **Wide rows** — side-by-side callouts should stack vertically. If a scene uses
  horizontal layout, branch on aspect ratio: read `useVideoConfig()` and switch
  `flexDirection`/sizes when `height > width`.
- **Safe area** — keep key text within the middle ~80%; phone UI (captions,
  buttons) overlaps the top/bottom ~10–15%.

For a distinct vertical layout rather than a reflow, make a dedicated wrapper
component that arranges the same scenes for portrait, and point `VideoVertical`
at it.

## Square 1:1

Add another `<Composition id="VideoSquare">` at 1080×1080 the same way if a feed
post is wanted.

## Captions / subtitles

Short-form thrives on burned-in captions:
- **Manual** — hold caption lines in an array with start/end frames; render the
  active line near the lower third, big and high-contrast (white text, dark
  stroke/box). Animate word pop for energy.
- **From audio** — if there's a voiceover, transcribe with `@remotion/install-whisper-cpp`
  (Remotion's captioning helper) to get word-level timings, then render each
  word synced. Only pull this in when there's real narration.

Style captions for muted autoplay: most viewers watch without sound, so the
message must land on screen alone.

## Length & pacing

Short-form wants a hook in the first ~1s and total length ~10–30s. Cut slack
scenes, speed entrances, and lead with the payoff rather than building to it.
