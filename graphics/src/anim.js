import {Easing, interpolate} from 'remotion';

const ease = Easing.out(Easing.cubic);

// Eased 0..1 progress between two frames.
export const progress = (frame, start, end) =>
  interpolate(frame, [start, end], [0, 1], {
    easing: ease,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

// Fade in at the start and out at the end of a clip.
export const clipOpacity = (frame, duration, fadeIn = 12, fadeOut = 12) => {
  const a = interpolate(frame, [0, Math.max(1, fadeIn)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const b = interpolate(frame, [duration - Math.max(1, fadeOut), duration], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return Math.min(a, b);
};
