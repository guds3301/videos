import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {colorFor, palette, sansFont} from './theme.js';
import {clipOpacity, progress} from './anim.js';

// Short chapter card: small amber number, wide-tracked white title, thin steel rule that draws in.
// Transparent background so it sits over footage. No glow, no motion blur.
export const ChapterTitle = ({
  number = '01',
  title = 'CHAPTER TITLE',
  subtitle = '',
  position = 'lower_left', // lower_left | center
  accent = 'amber',
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, width, height} = useVideoConfig();
  const opacity = clipOpacity(frame, durationInFrames);
  const rule = progress(frame, 4, 28);
  const text = progress(frame, 8, 30);
  const centered = position === 'center';
  const margin = Math.round(width * 0.07);

  return (
    <AbsoluteFill style={{background: 'transparent', opacity}}>
      <div
        style={{
          position: 'absolute',
          left: centered ? 0 : margin,
          right: centered ? 0 : undefined,
          bottom: centered ? undefined : Math.round(height * 0.14),
          top: centered ? '50%' : undefined,
          transform: centered ? 'translateY(-50%)' : undefined,
          display: 'flex',
          flexDirection: 'column',
          alignItems: centered ? 'center' : 'flex-start',
          fontFamily: sansFont,
          color: palette.white,
          textShadow: `0 2px 18px ${palette.black}`,
        }}
      >
        <div
          style={{
            fontSize: 30,
            fontWeight: 600,
            letterSpacing: '0.32em',
            color: colorFor(accent),
            opacity: text,
            transform: `translateY(${(1 - text) * 10}px)`,
          }}
        >
          {number}
        </div>
        <div
          style={{
            height: 2,
            margin: '16px 0 20px',
            background: palette.steel,
            alignSelf: centered ? 'center' : 'flex-start',
            width: Math.round(rule * 520),
          }}
        />
        <div
          style={{
            fontSize: 72,
            fontWeight: 600,
            letterSpacing: '0.14em',
            textTransform: 'uppercase',
            opacity: text,
            transform: `translateY(${(1 - text) * 14}px)`,
          }}
        >
          {title}
        </div>
        {subtitle ? (
          <div
            style={{
              marginTop: 14,
              fontSize: 34,
              fontWeight: 400,
              letterSpacing: '0.04em',
              color: palette.steel,
              opacity: text,
            }}
          >
            {subtitle}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
