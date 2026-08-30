import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {COLORS, FONT_STACK, FONT_LIGHT} from '../theme';

// TODO: subject — closing logo/name, tagline, and the call to action.
const NAME = 'YOUR TITLE';
const TAGLINE = 'A short closing line';
const CTA = 'LEARN MORE';
const URL = 'yoursite.com';

export const OutroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const logo = spring({frame: frame - 3, fps, config: {damping: 11, stiffness: 120}});
  const ring = spring({frame: frame - 3, fps, config: {damping: 30, stiffness: 60}});
  const tagline = interpolate(frame, [24, 38], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cta = spring({frame: frame - 45, fps, config: {damping: 14, stiffness: 140}});
  const shimmer = interpolate((frame - 50) % 70, [0, 70], [-140, 620]);

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 50%, #10102a 0%, ${COLORS.bgDeep} 70%)`,
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      {/* Expanding ring burst behind the logo. */}
      <div
        style={{
          position: 'absolute',
          width: interpolate(ring, [0, 1], [100, 1500]),
          height: interpolate(ring, [0, 1], [100, 1500]),
          borderRadius: '50%',
          border: `3px solid rgba(0,229,255,${interpolate(ring, [0, 1], [0.8, 0])})`,
        }}
      />
      <div
        style={{
          fontFamily: FONT_STACK,
          fontSize: 150,
          fontWeight: 900,
          letterSpacing: 6,
          color: COLORS.white,
          transform: `scale(${logo})`,
          opacity: logo,
          textShadow: `0 0 80px ${COLORS.accent1}88`,
          textAlign: 'center',
        }}
      >
        {NAME}
      </div>
      <div
        style={{
          fontFamily: FONT_LIGHT,
          fontSize: 38,
          fontWeight: 300,
          letterSpacing: 8,
          color: COLORS.dim,
          marginTop: 10,
          opacity: tagline,
          textTransform: 'uppercase',
        }}
      >
        {TAGLINE}
      </div>
      {/* Call-to-action pill with a repeating shimmer sweep. */}
      <div
        style={{
          marginTop: 64,
          transform: `scale(${cta})`,
          opacity: cta,
          position: 'relative',
          overflow: 'hidden',
          borderRadius: 60,
          border: `2px solid ${COLORS.accent2}`,
          padding: '20px 64px',
          background: 'rgba(255,46,154,0.08)',
        }}
      >
        <div
          style={{
            fontFamily: FONT_STACK,
            fontSize: 48,
            fontWeight: 900,
            letterSpacing: 10,
            color: COLORS.accent2,
          }}
        >
          {CTA}
        </div>
        <div
          style={{
            position: 'absolute',
            top: 0,
            bottom: 0,
            left: shimmer,
            width: 90,
            background:
              'linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent)',
            transform: 'skewX(-18deg)',
          }}
        />
      </div>
      <div
        style={{
          position: 'absolute',
          bottom: 60,
          fontFamily: FONT_LIGHT,
          fontSize: 30,
          letterSpacing: 8,
          color: 'rgba(255,255,255,0.35)',
          opacity: interpolate(frame, [60, 75], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
        }}
      >
        {URL}
      </div>
    </AbsoluteFill>
  );
};
