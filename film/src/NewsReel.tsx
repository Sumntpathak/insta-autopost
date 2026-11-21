// Text-only tech news reel (15 s, 30 fps, 1080x1920): the outlet's own headline and first summary sentence are typed out,
// then the source is credited. Props come from reels/shipstack/news_feed.py (never invented). Same dark Studio look.
import {loadFont} from '@remotion/fonts';
import {Audio} from '@remotion/media';
import React from 'react';
import {AbsoluteFill, Easing, Sequence, continueRender, delayRender, interpolate, staticFile, useCurrentFrame} from 'remotion';

const C = {bg: '#0D1117', panel: '#161B22', line: '#2A313C', text: '#E6EDF3', soft: '#B6C0CC', muted: '#8B949E', accent: '#22D3EE', hot: '#F85149'};
const SANS = 'Geist, sans-serif';
const MONO = '"Geist Mono", monospace';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ease = Easing.bezier(0.16, 1, 0.3, 1);
const FPS = 30;

const ready = delayRender('Loading Geist');
Promise.all([
  loadFont({family: 'Geist', url: staticFile('fonts/Geist-Variable.ttf'), weight: '100 900'}),
  loadFont({family: 'Geist Mono', url: staticFile('fonts/GeistMono-Variable.ttf'), weight: '100 900'}),
]).then(() => continueRender(ready));

export type NewsProps = {
  source: string; headline: string; summary: string; date: string; domain: string;
  music?: string; musicVolume?: number; keyGain?: number;
};
export const newsDefaults: NewsProps = {
  source: 'BBC News', headline: 'Sample headline from the outlet appears here', summary: 'The first sentence of the outlet summary appears here.',
  date: '21 NOV 2026', domain: 'bbc.co.uk',
};

const typedCount = (frame: number, startSec: number, text: string, cps: number) =>
  Math.max(0, Math.min(text.length, Math.floor((frame - startSec * FPS) * cps / FPS) + 1));
const keyFrames = (startSec: number, text: string, cps: number) => {
  const out: number[] = [];
  for (let i = 0; i < text.length; i++) if (text[i] !== ' ') out.push(Math.round(startSec * FPS + i * FPS / cps));
  return out;
};
const Cursor: React.FC<{h: number}> = ({h}) => {
  const frame = useCurrentFrame();
  return <span style={{display: 'inline-block', width: h * 0.28, height: h * 0.9, marginLeft: 8, background: C.accent,
    opacity: Math.floor(frame / 15) % 2 === 0 ? 1 : 0, verticalAlign: 'text-bottom'}} />;
};

export const NewsReel: React.FC<Partial<NewsProps>> = (p) => {
  const d = {...newsDefaults, ...p} as NewsProps;
  const frame = useCurrentFrame();
  const sec = frame / FPS;
  const T = {head: 0.5, sum: 5.4, src: 9.8, cta: 12.6};
  const headCps = Math.min(34, Math.max(22, d.headline.length / 4));        // headline always finishes by ~4.5 s
  const sumCps = 46;
  const headN = typedCount(frame, T.head, d.headline, headCps);
  const sumN = typedCount(frame, T.sum, d.summary, sumCps);
  const headDone = T.head + d.headline.length / headCps;
  const sumDone = T.sum + d.summary.length / sumCps;
  const cta = 'Follow for daily tech news.';
  const ctaN = typedCount(frame, T.cta, cta, 32);
  const src = interpolate(sec, [T.src, T.src + 0.45], [0, 1], {...clamp, easing: ease});
  const rule = interpolate(sec, [headDone, headDone + 0.5], [0, 1], {...clamp, easing: Easing.bezier(0.65, 0, 0.35, 1)});
  const keys = [...keyFrames(T.head, d.headline, headCps), ...keyFrames(T.sum, d.summary, sumCps), ...keyFrames(T.cta, cta, 32)];

  return (
    <AbsoluteFill style={{background: C.bg, color: C.text, fontFamily: SANS, overflow: 'hidden'}}>
      <AbsoluteFill style={{backgroundImage: `linear-gradient(${C.line}33 1px, transparent 1px), linear-gradient(90deg, ${C.line}33 1px, transparent 1px)`,
        backgroundSize: '90px 90px', opacity: 0.5}} />
      <AbsoluteFill style={{background: `radial-gradient(900px 700px at ${30 + Math.sin(sec * 0.6) * 8}% ${18 + Math.cos(sec * 0.5) * 4}%, ${C.accent}22, transparent 70%)`}} />

      <div style={{position: 'absolute', left: 80, right: 80, top: 100, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        fontFamily: MONO, fontSize: 28, letterSpacing: 3, color: C.muted, opacity: interpolate(sec, [0, 0.4], [0, 1], clamp)}}>
        <span style={{color: C.accent}}>TECH NEWS</span><span>{d.date}</span>
      </div>

      <div style={{position: 'absolute', left: 80, right: 80, top: 300, display: 'flex', flexDirection: 'column', gap: 56}}>
        <div style={{fontWeight: 800, fontSize: 84, letterSpacing: -2.5, lineHeight: 1.06}}>
          {d.headline.slice(0, headN)}{headN < d.headline.length ? <Cursor h={84} /> : null}
        </div>
        <div style={{height: 6, width: 920 * rule, background: C.accent, borderRadius: 3}} />
        <div style={{fontSize: 46, lineHeight: 1.3, color: C.soft, fontWeight: 500, opacity: interpolate(sec, [T.sum - 0.1, T.sum + 0.2], [0, 1], clamp)}}>
          {d.summary.slice(0, sumN)}{sumN > 0 && sumN < d.summary.length ? <Cursor h={46} /> : null}
        </div>
      </div>

      <div style={{position: 'absolute', left: 80, right: 80, top: 1470, height: 210, opacity: src, translate: `0px ${(1 - src) * 40}px`,
        background: C.panel, border: `2px solid ${C.line}`, borderRadius: 28, padding: '0 40px', display: 'flex', alignItems: 'center', gap: 32}}>
        <div style={{width: 12, height: 90, background: C.accent, borderRadius: 6}} />
        <div style={{display: 'flex', flexDirection: 'column', gap: 8, minWidth: 0}}>
          <div style={{fontFamily: MONO, fontSize: 26, letterSpacing: 3, color: C.muted}}>SOURCE</div>
          <div style={{fontSize: 52, fontWeight: 800, letterSpacing: -1, whiteSpace: 'nowrap'}}>{d.source}</div>
          <div style={{fontFamily: MONO, fontSize: 28, color: C.accent}}>{d.domain}</div>
        </div>
      </div>

      <div style={{position: 'absolute', left: 80, right: 80, top: 1810, fontFamily: MONO, fontSize: 30, color: C.muted, letterSpacing: 1,
        display: 'flex', justifyContent: 'space-between'}}>
        <span>{cta.slice(0, ctaN)}</span><span style={{color: C.accent, opacity: sec > T.cta ? 1 : 0}}>@shipstack_</span>
      </div>

      {d.music ? <Audio src={staticFile(`bgm/${d.music}`)} loop volume={(f) => (d.musicVolume ?? 0.4) * interpolate(f, [0, 15, 420, 450], [0, 1, 1, 0], clamp)} /> : null}
      {keys.map((k, i) => (
        <Sequence key={i} from={k} durationInFrames={6} layout="none">
          <Audio src={staticFile(`sfx/key${i % 3}.wav`)} volume={(0.55 + (i % 5) * 0.06) * (d.keyGain ?? 1)} />
        </Sequence>
      ))}
      <Sequence from={Math.round(headDone * FPS)} durationInFrames={12} layout="none"><Audio src={staticFile('sfx/done.wav')} volume={0.4} /></Sequence>
      <Sequence from={Math.round(T.src * FPS)} durationInFrames={30} layout="none"><Audio src={staticFile('sfx/result.wav')} volume={0.5} /></Sequence>
    </AbsoluteFill>
  );
};
