# Add-on: Audio (music + SFX)

Renders are **silent by default**. Add sound with Remotion's `<Audio>` /
`<Sequence>` — audio is placed on the timeline just like visuals. No assets are
bundled with this skill (licensing), so you source the files; this doc covers
sourcing and wiring.

## Wiring it up

1. Put audio files in a `public/` folder at the project root
   (`public/music.mp3`, `public/sfx/whoosh.mp3`).
2. Reference them with `staticFile()` and place with `<Audio>`:

```tsx
import {Audio, Sequence, staticFile, interpolate} from 'remotion';

// Background music for the whole piece (already stubbed in Video.tsx):
<Audio src={staticFile('music.mp3')} volume={0.7} />

// A one-shot SFX at a specific moment — start it with a <Sequence>:
<Sequence from={TITLE_END}>
  <Audio src={staticFile('sfx/whoosh.mp3')} />
</Sequence>
```

3. Ensure the composition is long enough for the audio, or trim audio with
   `startFrom`/`endAt` (in frames) on `<Audio>`.

## Syncing to scene cuts

The scene boundaries live in `src/config.ts` (`TITLE_END`, `CONTENT_END`, …).
Place transition SFX (whoosh/impact) at those exact frames with a `<Sequence
from={BOUNDARY}>` so hits land on the cuts and the `Flash` overlay. This is what
makes a promo feel "designed" rather than a track laid under silence.

## Ducking & fades

- **Fade in/out** music with a frame-driven `volume` callback:
  ```tsx
  <Audio src={staticFile('music.mp3')} volume={(f) =>
    interpolate(f, [0, 15, durationInFrames - 20, durationInFrames],
      [0, 0.7, 0.7, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})} />
  ```
- **Duck** music under a voiceover by lowering its `volume` during the VO
  `<Sequence>` range (same interpolate trick keyed off the frame).

## Sourcing (royalty-free)

Do not use copyrighted tracks. Point the user to royalty-free/CC0 sources and
let them pick and drop the file in `public/`:
- Music: YouTube Audio Library, Pixabay Music, Free Music Archive (check CC
  terms), Uppbeat, Incompetech.
- SFX: Pixabay, freesound.org (mind the license per clip), Mixkit.
Keep the license/attribution note with the project if the license requires it.

## Rendering with audio

No extra flags — `npx remotion render Video out/video.mp4` muxes the audio in.
If a render is unexpectedly silent, check: file is in `public/`, `staticFile()`
path matches, the `<Audio>` isn't past the composition's duration, and `volume`
isn't 0 at those frames. When reporting the final video, state that it has sound.
