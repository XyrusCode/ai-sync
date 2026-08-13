import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  random,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {COLORS, FONT_STACK, FONT_LIGHT} from '../theme';

// TODO: subject — the headline and kicker for the opening scene.
const TITLE = 'YOUR TITLE';
const KICKER = 'A SHORT TAGLINE';

// Neon particles that converge toward the center as the title builds.
const Particles: React.FC = () => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const accents = [COLORS.accent1, COLORS.accent2, COLORS.accent3];
  return (
    <AbsoluteFill>
      {Array.from({length: 40}).map((_, i) => {
        const seed = `p-${i}`;
        const startX = random(seed + 'x') * width;
        const startY = random(seed + 'y') * height;
        const t = interpolate(frame, [0, 40 + random(seed + 'd') * 20], [0, 1], {
          extrapolateRight: 'clamp',
        });
        const x = interpolate(t, [0, 1], [startX, width / 2]);
        const y = interpolate(t, [0, 1], [startY, height / 2]);
        const opacity = interpolate(t, [0, 0.7, 1], [0, 0.9, 0]);
        const size = 2 + random(seed + 's') * 5;
        const color = accents[i % accents.length];
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: size,
              height: size,
              borderRadius: '50%',
              backgroundColor: color,
              opacity,
              boxShadow: `0 0 ${size * 3}px ${color}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

export const TitleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const letters = TITLE.split('');

  const underline = spring({frame: frame - 40, fps, config: {damping: 200}});
  const kickerOpacity = interpolate(frame, [50, 65], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 50%, #101025 0%, ${COLORS.bgDeep} 70%)`,
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <Particles />
      {/* Title builds letter-by-letter with a spring rise + blur-in. */}
      <div style={{display: 'flex', gap: 4, flexWrap: 'wrap', justifyContent: 'center'}}>
        {letters.map((letter, i) => {
          const s = spring({
            frame: frame - (10 + i * 4),
            fps,
            config: {damping: 12, stiffness: 160, mass: 0.6},
          });
          return (
            <span
              key={i}
              style={{
                fontFamily: FONT_STACK,
                fontSize: 180,
                fontWeight: 900,
                color: COLORS.white,
                transform: `translateY(${interpolate(s, [0, 1], [160, 0])}px) scale(${0.6 + s * 0.4})`,
                opacity: s,
                filter: `blur(${interpolate(s, [0, 1], [18, 0])}px)`,
                textShadow: `0 0 40px rgba(255,255,255,0.35)`,
                letterSpacing: 2,
                display: 'inline-block',
                whiteSpace: 'pre',
              }}
            >
              {letter}
            </span>
          );
        })}
      </div>
      <div
        style={{
          width: interpolate(underline, [0, 1], [0, 640]),
          height: 8,
          marginTop: 24,
          borderRadius: 4,
          background: `linear-gradient(90deg, ${COLORS.accent1}, ${COLORS.accent2})`,
          boxShadow: `0 0 30px ${COLORS.accent2}`,
        }}
      />
      <div
        style={{
          marginTop: 30,
          fontFamily: FONT_LIGHT,
          fontSize: 40,
          fontWeight: 300,
          letterSpacing: 18,
          color: COLORS.dim,
          opacity: kickerOpacity,
          textTransform: 'uppercase',
          textAlign: 'center',
        }}
      >
        {KICKER}
      </div>
    </AbsoluteFill>
  );
};
