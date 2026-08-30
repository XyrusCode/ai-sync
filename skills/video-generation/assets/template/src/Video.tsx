import React from 'react';
import {AbsoluteFill, Sequence, interpolate, useCurrentFrame} from 'remotion';
import {COLORS} from './theme';
import {TITLE_END, CONTENT_END, OUTRO_END} from './config';
import {TitleScene} from './scenes/TitleScene';
import {ContentScene} from './scenes/ContentScene';
import {OutroScene} from './scenes/OutroScene';

// Optional soundtrack: drop a file in public/ and uncomment. See references/audio.md.
// import {Audio, staticFile} from 'remotion';

// A quick white flash sells the cut between scenes. Reuse at each boundary.
const Flash: React.FC<{at: number}> = ({at}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [at - 3, at, at + 5], [0, 0.85, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  if (opacity <= 0.01) return null;
  return <AbsoluteFill style={{backgroundColor: COLORS.white, opacity}} />;
};

export const Video: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: COLORS.bg}}>
      {/* <Audio src={staticFile('music.mp3')} volume={0.7} /> */}

      <Sequence from={0} durationInFrames={TITLE_END}>
        <TitleScene />
      </Sequence>
      <Sequence from={TITLE_END} durationInFrames={CONTENT_END - TITLE_END}>
        <ContentScene />
      </Sequence>
      <Sequence from={CONTENT_END} durationInFrames={OUTRO_END - CONTENT_END}>
        <OutroScene />
      </Sequence>

      <Flash at={TITLE_END} />
      <Flash at={CONTENT_END} />
    </AbsoluteFill>
  );
};
