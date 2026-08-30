import {Composition} from 'remotion';
import {Video} from './Video';
import {
  DURATION_IN_FRAMES,
  FPS,
  WIDTH,
  HEIGHT,
  VERTICAL_WIDTH,
  VERTICAL_HEIGHT,
} from './config';

// Two compositions share the same <Video> content at different aspect ratios.
// - "Video"          -> 16:9 landscape (YouTube, web)
// - "VideoVertical"  -> 9:16 vertical  (Reels / TikTok / Shorts)
// The id you pass to `remotion render <id>` must match one of these exactly.
export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="Video"
        component={Video}
        durationInFrames={DURATION_IN_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
      <Composition
        id="VideoVertical"
        component={Video}
        durationInFrames={DURATION_IN_FRAMES}
        fps={FPS}
        width={VERTICAL_WIDTH}
        height={VERTICAL_HEIGHT}
      />
    </>
  );
};
