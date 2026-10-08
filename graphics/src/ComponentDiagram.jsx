import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {colorFor, palette, sansFont} from './theme.js';
import {clipOpacity, progress} from './anim.js';

// One-idea component diagram. Elements appear in stages so labels are added gradually.
// nodes: {id, label, x, y, w, h, stage?, highlight?}   (x,y = center; all values 0..1 of the frame)
// links: {from, to, label?, stage?, highlight?}
// Set illustrative=true for a reconstruction or simplified model: the frame is tagged as such.
export const ComponentDiagram = ({
  title = '',
  nodes = [],
  links = [],
  stageFrames = 24,
  illustrative = true,
  accent = 'amber',
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, width, height} = useVideoConfig();
  const opacity = clipOpacity(frame, durationInFrames, 14, 14);
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const appear = (stage = 0) => progress(frame, 8 + stage * stageFrames, 8 + stage * stageFrames + 16);
  const color = colorFor(accent);

  const box = (n) => ({
    cx: n.x * width,
    cy: n.y * height,
    hw: (n.w * width) / 2,
    hh: (n.h * height) / 2,
  });

  // Point where the segment from box a's center toward (tx,ty) leaves box a.
  const edge = (a, tx, ty) => {
    const dx = tx - a.cx;
    const dy = ty - a.cy;
    const sx = dx === 0 ? Infinity : a.hw / Math.abs(dx);
    const sy = dy === 0 ? Infinity : a.hh / Math.abs(dy);
    const s = Math.min(sx, sy);
    return {x: a.cx + dx * s, y: a.cy + dy * s};
  };

  return (
    <AbsoluteFill style={{background: 'transparent', opacity}}>
      {title ? (
        <div
          style={{
            position: 'absolute',
            left: width * 0.07,
            top: height * 0.07,
            fontFamily: sansFont,
            fontSize: 30,
            fontWeight: 600,
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
            color: palette.white,
            opacity: appear(0),
            textShadow: `0 2px 14px ${palette.black}`,
          }}
        >
          {title}
        </div>
      ) : null}

      <svg width={width} height={height} style={{position: 'absolute', inset: 0}}>
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="18" markerHeight="18" markerUnits="userSpaceOnUse" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill={palette.steel} />
          </marker>
          <marker id="arrow-hi" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="18" markerHeight="18" markerUnits="userSpaceOnUse" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill={color} />
          </marker>
        </defs>
        {links.map((l, i) => {
          const a = byId[l.from];
          const b = byId[l.to];
          if (!a || !b) return null;
          const A = box(a);
          const B = box(b);
          const p1 = edge(A, B.cx, B.cy);
          const p2 = edge(B, A.cx, A.cy);
          const t = appear(l.stage ?? 1);
          const x2 = p1.x + (p2.x - p1.x) * t;
          const y2 = p1.y + (p2.y - p1.y) * t;
          return (
            <line
              key={`l${i}`}
              x1={p1.x}
              y1={p1.y}
              x2={x2}
              y2={y2}
              stroke={l.highlight ? color : palette.steel}
              strokeWidth={l.highlight ? 4 : 3}
              markerEnd={t > 0.98 ? (l.highlight ? 'url(#arrow-hi)' : 'url(#arrow)') : undefined}
            />
          );
        })}
        {nodes.map((n) => {
          const b = box(n);
          const t = appear(n.stage ?? 0);
          return (
            <rect
              key={n.id}
              x={b.cx - b.hw}
              y={b.cy - b.hh}
              width={b.hw * 2}
              height={b.hh * 2}
              rx={6}
              fill={palette.graphite}
              fillOpacity={0.82 * t}
              stroke={n.highlight ? color : palette.steel}
              strokeWidth={n.highlight ? 4 : 2}
              strokeOpacity={t}
            />
          );
        })}
      </svg>

      {nodes.map((n) => {
        const b = box(n);
        const t = appear((n.stage ?? 0) + 0.5);
        return (
          <div
            key={`t${n.id}`}
            style={{
              position: 'absolute',
              left: b.cx - b.hw,
              top: b.cy - b.hh,
              width: b.hw * 2,
              height: b.hh * 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              fontFamily: sansFont,
              fontSize: 30,
              fontWeight: 600,
              letterSpacing: '0.06em',
              color: n.highlight ? color : palette.white,
              opacity: t,
              padding: 8,
            }}
          >
            {n.label}
          </div>
        );
      })}

      {links
        .filter((l) => l.label && byId[l.from] && byId[l.to])
        .map((l, i) => {
          const A = box(byId[l.from]);
          const B = box(byId[l.to]);
          const p1 = edge(A, B.cx, B.cy);
          const p2 = edge(B, A.cx, A.cy);
          const t = appear((l.stage ?? 1) + 0.6);
          return (
            <div
              key={`ll${i}`}
              style={{
                position: 'absolute',
                left: (p1.x + p2.x) / 2,
                top: (p1.y + p2.y) / 2 - 36,
                transform: 'translateX(-50%)',
                fontFamily: sansFont,
                fontSize: 24,
                fontWeight: 500,
                letterSpacing: '0.1em',
                color: palette.steel,
                opacity: t,
                textShadow: `0 2px 12px ${palette.black}`,
                whiteSpace: 'nowrap',
              }}
            >
              {l.label}
            </div>
          );
        })}

      {illustrative ? (
        <div
          style={{
            position: 'absolute',
            right: width * 0.07,
            bottom: height * 0.07,
            fontFamily: sansFont,
            fontSize: 22,
            letterSpacing: '0.22em',
            color: palette.steel,
            opacity: appear(0),
            textShadow: `0 2px 12px ${palette.black}`,
          }}
        >
          SIMPLIFIED MODEL
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
