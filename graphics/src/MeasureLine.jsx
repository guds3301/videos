import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {colorFor, palette, sansFont} from './theme.js';
import {clipOpacity, progress} from './anim.js';

// Dimension line between two normalized points with end ticks and a value label.
// Use it to give a truthful scale cue over real footage. Transparent background.
export const MeasureLine = ({
  label = 'LENGTH',
  value = '12.4',
  unit = 'm',
  from = {x: 0.3, y: 0.7},
  to = {x: 0.7, y: 0.7},
  accent = 'amber',
  illustrative = false,
  labelSide = 'below', // below | above (relative to a left-to-right line)
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, width, height} = useVideoConfig();
  const opacity = clipOpacity(frame, durationInFrames);
  const draw = progress(frame, 4, 30);
  const text = progress(frame, 22, 40);

  const x1 = from.x * width;
  const y1 = from.y * height;
  const x2 = to.x * width;
  const y2 = to.y * height;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy) || 1;
  const nx = -dy / len; // unit normal
  const ny = dx / len;
  const tick = 22;
  const ex = x1 + dx * draw;
  const ey = y1 + dy * draw;
  const color = colorFor(accent);
  // The label block is ~150 px tall; offset it so it never touches the line.
  const side = labelSide === 'above' ? -1 : 1;
  const mx = (x1 + x2) / 2 + nx * 110 * side;
  const my = (y1 + y2) / 2 + ny * 110 * side;
  const angle = (Math.atan2(dy, dx) * 180) / Math.PI;
  const upright = angle > 90 || angle < -90 ? angle + 180 : angle;

  return (
    <AbsoluteFill style={{background: 'transparent', opacity}}>
      <svg width={width} height={height} style={{position: 'absolute', inset: 0}}>
        <line x1={x1} y1={y1} x2={ex} y2={ey} stroke={color} strokeWidth={3} strokeLinecap="butt" />
        <line x1={x1 - nx * tick} y1={y1 - ny * tick} x2={x1 + nx * tick} y2={y1 + ny * tick} stroke={color} strokeWidth={3} />
        <line
          x1={ex - nx * tick}
          y1={ey - ny * tick}
          x2={ex + nx * tick}
          y2={ey + ny * tick}
          stroke={color}
          strokeWidth={3}
          opacity={draw > 0.02 ? 1 : 0}
        />
      </svg>
      <div
        style={{
          position: 'absolute',
          left: mx,
          top: my,
          transform: `translate(-50%, -50%) rotate(${upright}deg)`,
          fontFamily: sansFont,
          textAlign: 'center',
          opacity: text,
          textShadow: `0 2px 14px ${palette.black}`,
          whiteSpace: 'nowrap',
        }}
      >
        <div style={{fontSize: 26, fontWeight: 500, letterSpacing: '0.18em', color: palette.steel, textTransform: 'uppercase'}}>
          {label}
        </div>
        <div style={{fontSize: 56, fontWeight: 600, color: palette.white, marginTop: 4}}>
          {value}
          <span style={{fontSize: 34, fontWeight: 500, color, marginLeft: 8}}>{unit}</span>
        </div>
        {illustrative ? (
          <div style={{fontSize: 20, letterSpacing: '0.2em', color: palette.steel, marginTop: 6}}>ILLUSTRATIVE</div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
