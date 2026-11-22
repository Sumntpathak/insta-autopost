import React from 'react';
import {Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, FPS, SANS, SERIF} from './brand';

export const sec = (x: number) => Math.round(x * FPS);
const ease = Easing.bezier(0.22, 1, 0.36, 1);
export const tw = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, b], [from, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});

/** opacity window in seconds with 0.45s fade in / 0.4s fade out */
export const useWin = (a: number, b: number) => {
  const f = useCurrentFrame();
  return Math.min(tw(f, sec(a), sec(a + 0.45)), tw(f, sec(b - 0.4), sec(b), 1, 0));
};
export const useSp = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (atSec: number, damping = 16) => spring({frame: f - sec(atSec), fps, config: {damping, stiffness: 120}});
};

export const ICONS: Record<string, React.ReactNode> = {
  check: <path d="M5 12.5l4.5 4.5L19 7" />,
  flame: <path d="M12 2.5c.8 3.6-3.2 4.8-3.2 9a3.2 3.2 0 006.4 0c0-1.2-.5-1.9-1-2.7-.4 1-1.1 1.6-2 1.6 1-2.3.7-5.2-.2-7.9z" />,
  drop: <path d="M12 3s-6 7-6 11.2a6 6 0 0012 0C18 10 12 3 12 3z" />,
  thermo: <><path d="M10 14.5V5a2 2 0 014 0v9.5a4 4 0 11-4 0z" /><path d="M12 9v7" /></>,
  candy: <path d="M12 3l9 9-9 9-9-9z" />,
  bowl: <><path d="M3 11h18a9 9 0 01-18 0z" /><path d="M9 6c0-1.5 1-1.5 1-3M14 6c0-1.5 1-1.5 1-3" /></>,
  ring: <><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="3" /></>,
  soft: <path d="M4 14c3-6 5 6 8 0s5 6 8 0" />,
  virus: <><circle cx="12" cy="12" r="4.5" /><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" /></>,
  rub: <path d="M3 12h18M7 8l-4 4 4 4M17 8l4 4-4 4" />,
  saw: <path d="M3 18l3.2-10 3.2 10 3.2-10 3.2 10 3.2-10" />,
  smoke: <><path d="M3 15h13v4H3zM18 15h3v4h-3z" /><path d="M8 11c0-2 2-2 2-4s-2-2-2-4" /></>,
  glass: <path d="M6 3h12l-6 9zM12 12v8M8 20h8" />,
  alert: <><path d="M12 3.5l9.5 16.5h-19z" /><path d="M12 10v4.5M12 17.5v.3" /></>,
  heart: <path d="M12 20s-8-5-8-10.5A4.5 4.5 0 0112 7a4.5 4.5 0 018 2.5C20 15 12 20 12 20z" />,
  pill: <><rect x="3" y="9" width="18" height="6" rx="3" transform="rotate(-35 12 12)" /><path d="M9 15l6-6" /></>,
  home: <path d="M4 11l8-7 8 7v9H4zM10 20v-6h4v6" />,
  ban: <><circle cx="12" cy="12" r="8.5" /><path d="M6 6l12 12" /></>,
};
export const Icon = ({name, size = 30, color = '#fff'}: {name: string; size?: number; color?: string}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">{ICONS[name]}</svg>
);

export const glass = (accent: string): React.CSSProperties => ({
  background: 'linear-gradient(145deg, rgba(110,18,44,.86), rgba(54,8,26,.88))',
  backdropFilter: 'blur(16px) saturate(1.2)',
  border: '1px solid rgba(255,255,255,.22)',
  borderTop: `5px solid ${accent}`,
  borderRadius: 26,
  boxShadow: '0 24px 60px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.18)',
});

export type Item = {icon: string; text: string; at: number};
/** Glass info panel; items pop in at their own `at` second so they sync with speech. */
export const Panel = ({side, start, end, title, eyebrow, items, accent = C.teal, width = 470, top = 150}: {
  side: 'left' | 'right'; start: number; end: number; title: string; eyebrow?: string; items: Item[]; accent?: string; width?: number; top?: number;
}) => {
  const o = useWin(start, end);
  const sp = useSp();
  if (o <= 0.001) return null;
  const dir = side === 'left' ? -1 : 1;
  return (
    <div style={{position: 'absolute', [side]: 44, top, width, opacity: o, transform: `translateX(${(1 - sp(start)) * dir * 120}px)`, ...glass(accent), padding: '24px 26px 22px'}}>
      {eyebrow && <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 19, letterSpacing: 4, color: accent, marginBottom: 6}}>{eyebrow}</div>}
      <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 40, lineHeight: 1.15, color: C.cream, marginBottom: 16}}>{title}</div>
      {items.map((it, i) => {
        const p = Math.max(0, sp(it.at, 14));
        if (p <= 0.001) return null;
        return (
          <div key={i} style={{display: 'flex', alignItems: 'center', gap: 16, padding: '11px 0', borderTop: '1px solid rgba(255,255,255,.14)',
            opacity: p, transform: `translateY(${(1 - p) * 18}px) scale(${0.96 + 0.04 * p})`}}>
            <div style={{width: 54, height: 54, flex: '0 0 54px', borderRadius: 16, background: `${accent}33`, border: `1.5px solid ${accent}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center'}}><Icon name={it.icon} size={30} color={C.cream} /></div>
            <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 30, lineHeight: 1.2, color: '#fff'}}>{it.text}</div>
          </div>
        );
      })}
    </div>
  );
};

/** Wide glass banner at the lower centre. */
export const Banner = ({start, end, big, small, accent = C.gold, icon}: {start: number; end: number; big: string; small?: string; accent?: string; icon: string}) => {
  const o = useWin(start, end);
  const sp = useSp();
  if (o <= 0.001) return null;
  return (
    <div style={{position: 'absolute', left: 260, right: 260, bottom: 70, opacity: o, transform: `translateY(${(1 - sp(start)) * 60}px)`,
      ...glass(accent), padding: '24px 40px', display: 'flex', alignItems: 'center', gap: 28}}>
      <div style={{width: 84, height: 84, flex: '0 0 84px', borderRadius: 24, background: `${accent}2e`, border: `2px solid ${accent}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center'}}><Icon name={icon} size={46} color={accent} /></div>
      <div>
        <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 52, lineHeight: 1.1, color: C.cream}}>{big}</div>
        {small && <div style={{fontFamily: SANS, fontWeight: 500, fontSize: 28, color: '#ffffffcc', marginTop: 6}}>{small}</div>}
      </div>
    </div>
  );
};
