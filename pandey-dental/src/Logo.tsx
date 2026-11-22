import {interpolate} from 'remotion';
import {C} from './brand';
// Shield + "P" + smile arc. No tooth. t: 0..1 draws it in. light=true for dark backgrounds.
export const Logo = ({size = 240, t = 1, light = false}: {size?: number; t?: number; light?: boolean}) => {
  const e = (a: number, b: number) => interpolate(t, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const shield = 'M100 6 C138 22 170 26 190 30 V112 C190 162 152 198 100 214 C48 198 10 162 10 112 V30 C30 26 62 22 100 6Z';
  const id = light ? 'lg-l' : 'lg-d';
  return (
    <svg width={size} height={size * 1.08} viewBox="0 0 200 216" style={{overflow: 'visible', filter: 'drop-shadow(0 10px 18px rgba(0,0,0,.35))'}}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={light ? '#FFF8EC' : '#9B1E42'} />
          <stop offset="1" stopColor={light ? '#EBD9BF' : C.maroonDeep} />
        </linearGradient>
      </defs>
      <path d={shield} fill={`url(#${id})`} opacity={e(0, 0.35)} />
      <path d={shield} fill="none" stroke={C.gold} strokeWidth={4} strokeDasharray={760} strokeDashoffset={760 * (1 - e(0, 0.6))} />
      <path d="M100 22 C130 34 156 38 172 40" fill="none" stroke="#fff" strokeOpacity={0.35} strokeWidth={3} strokeLinecap="round" opacity={e(0.5, 0.8)} />
      <path d="M76 150 V68 H108 C132 68 143 81 143 98 C143 115 132 128 108 128 H76" fill="none" stroke={light ? C.maroon : C.cream}
        strokeWidth={15} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={420} strokeDashoffset={420 * (1 - e(0.3, 0.8))} />
      <path d="M60 168 Q100 194 140 168" fill="none" stroke={C.teal} strokeWidth={9} strokeLinecap="round"
        strokeDasharray={130} strokeDashoffset={130 * (1 - e(0.7, 1))} />
    </svg>
  );
};
