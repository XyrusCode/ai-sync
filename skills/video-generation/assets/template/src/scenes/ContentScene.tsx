import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {COLORS, FONT_STACK, FONT_LIGHT} from '../theme';

// TODO: subject — the main points. 2-4 items reads best. Each gets its own color.
const HEADING = 'WHY IT MATTERS';
const ITEMS = [
  {label: 'POINT ONE', color: COLORS.accent1},
  {label: 'POINT TWO', color: COLORS.accent3},
  {label: 'POINT THREE', color: COLORS.accent2},
];

export const ContentScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const headingS = spring({frame, fps, config: {damping: 14, stiffness: 120}});

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 40%, #12122a 0%, ${COLORS.bgDeep} 75%)`,
        justifyContent: 'center',
        alignItems: 'center',
        gap: 40,
      }}
    >
      {/* Slow rotating accent ring for depth. */}
      <div
        style={{
          position: 'absolute',
          width: 900,
          height: 900,
          borderRadius: '50%',
          border: '2px solid rgba(255,255,255,0.06)',
          borderTopColor: COLORS.accent1,
          transform: `rotate(${frame * 0.8}deg)`,
        }}
      />
      <div
        style={{
          fontFamily: FONT_LIGHT,
          fontSize: 40,
          letterSpacing: 12,
          color: COLORS.dim,
          textTransform: 'uppercase',
          opacity: headingS,
          transform: `translateY(${interpolate(headingS, [0, 1], [-40, 0])}px)`,
        }}
      >
        {HEADING}
      </div>
      {/* Each item slides in from alternating sides, staggered. */}
      {ITEMS.map((item, i) => {
        const s = spring({
          frame: frame - (20 + i * 14),
          fps,
          config: {damping: 13, stiffness: 150},
        });
        const side = i % 2 === 0 ? -1 : 1;
        return (
          <div
            key={item.label}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 24,
              transform: `translateX(${interpolate(s, [0, 1], [side * 320, 0])}px) scale(${0.8 + s * 0.2})`,
              opacity: s,
            }}
          >
            <div
              style={{
                width: 22,
                height: 22,
                borderRadius: '50%',
                backgroundColor: item.color,
                boxShadow: `0 0 30px ${item.color}`,
              }}
            />
            <div
              style={{
                fontFamily: FONT_STACK,
                fontSize: 72,
                fontWeight: 900,
                color: COLORS.white,
                letterSpacing: 3,
                padding: '14px 44px',
                border: `2px solid ${item.color}`,
                borderRadius: 16,
                background: 'rgba(7,7,15,0.7)',
                boxShadow: `0 0 40px ${item.color}33`,
              }}
            >
              {item.label}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
