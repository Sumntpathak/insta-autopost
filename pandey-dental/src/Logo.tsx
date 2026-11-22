import {interpolate, useCurrentFrame} from 'remotion';
import {C} from './brand';
// Shield + "P" + smile curve. No tooth. `t` 0..1 draws it in.
export const Logo = ({size = 240, t = 1, dark = false}: {size?: number; t?: number; dark?: boolean}) => {
  const e = (a: number, b: number) => interpolate(t, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const fill = dark ? C.cream : C.maroon, stroke = dark ? C.maroon : C.cream;
  return (
    <svg width={size} height={size * 1.1} viewBox="0 0 200 220">
      <path d="M100 8 C140 24 172 26 188 30 V110 C188 160 150 196 100 212 C50 196 12 160 12 110 V30 C28 26 60 24 100 8Z"
        fill={fill} opacity={e(0, 0.4)} transform={`translate(100 110) scale(${0.85 + 0.15 * e(0, 0.4)}) translate(-100 -110)`} />
      <path d="M100 8 C140 24 172 26 188 30 V110 C188 160 150 196 100 212 C50 196 12 160 12 110 V30 C28 26 60 24 100 8Z"
        fill="none" stroke={C.teal} strokeWidth={5} strokeDasharray={900} strokeDashoffset={900 * (1 - e(0, 0.6))} />
      <path d="M78 150 V70 H108 C130 70 140 82 140 98 C140 114 130 126 108 126 H78" fill="none" stroke={stroke} strokeWidth={14}
        strokeLinecap="round" strokeLinejoin="round" strokeDasharray={400} strokeDashoffset={400 * (1 - e(0.35, 0.8))} />
      <path d="M62 168 Q100 190 138 168" fill="none" stroke={C.teal} strokeWidth={9} strokeLinecap="round"
        strokeDasharray={120} strokeDashoffset={120 * (1 - e(0.7, 1))} />
    </svg>
  );
};
export const useT = (start: number, dur: number) => {
  const f = useCurrentFrame();
  return interpolate(f, [start, start + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
};
