// Motion sample, scenes 1-2 of "View From the Top" (docs/screenplay.md):
// sunrise penthouse, the Guru from behind, then the camera tilts down to Tab Nagar.
import {Audio} from '@remotion/media';
import React from 'react';
import {AbsoluteFill, Easing, Sequence, interpolate, random, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

const SANS = 'Geist, sans-serif';
const MONO = '"Geist Mono", monospace';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export type Word = {text: string; start: number; end: number};
export type Scene1Props = {line1: string; line2: string; line1Dur: number; line2Dur: number; gap: number;
  words1: Word[]; words2: Word[]};

const WORLD_H = 3800;          // the camera travels down this tall world
const TILT_TO = -(WORLD_H - 1920);

// ------------------------------------------------------------ sky + skyline (top of the world)
const Sky: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const warm = interpolate(frame, [0, 8 * fps], [0, 1], clamp);
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: 2000,
      background: `linear-gradient(180deg, #120f2e 0%, #2b1d52 ${30 - warm * 8}%, #a8456b ${62 - warm * 6}%, #f29a5c ${80 - warm * 5}%, #ffd59a 100%)`}}>
      <div style={{position: 'absolute', left: 540 - 260, width: 520, height: 520, borderRadius: '50%',
        top: interpolate(frame, [0, 10 * fps], [1420, 1180], clamp),
        background: 'radial-gradient(circle, #fff3d1 0%, #ffd27a 35%, rgba(255,170,90,0.35) 60%, rgba(255,140,80,0) 72%)'}} />
    </div>
  );
};

const FarSkyline: React.FC = () => {
  const towers = Array.from({length: 18}, (_, i) => ({
    x: i * 64 - 20, w: 50 + random(`w${i}`) * 50, h: 180 + random(`h${i}`) * 420}));
  return (
    <svg width={1080} height={700} style={{position: 'absolute', left: 0, top: 1300}}>
      {towers.map((t, i) => <rect key={i} x={t.x} y={700 - t.h} width={t.w} height={t.h} fill="#1c1636" opacity={0.85} />)}
    </svg>
  );
};

// ------------------------------------------------------------ the balcony and the Guru
const Balcony: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const breathe = Math.sin((frame / fps) * 1.6) * 3;
  const sip = interpolate(frame % (6 * fps), [3 * fps, 3.6 * fps, 4.4 * fps], [0, -26, 0], clamp);
  return (
    <div style={{position: 'absolute', left: 0, top: 1100, width: 1080, height: 900}}>
      {/* infinity pool edge */}
      <div style={{position: 'absolute', left: 0, top: 640, width: 1080, height: 60,
        background: 'linear-gradient(180deg, #4fd2e8, #1a7d95)', opacity: 0.9}} />
      {/* glass railing panels */}
      {[0, 1, 2, 3].map((i) => (
        <div key={i} style={{position: 'absolute', left: i * 270 + 6, top: 470, width: 258, height: 190,
          background: 'linear-gradient(135deg, rgba(255,255,255,0.20), rgba(255,255,255,0.05))',
          borderTop: '6px solid rgba(255,240,220,0.75)'}} />
      ))}
      {/* the Guru, seen from behind: robe, head, glass of cutting chai */}
      <svg width={560} height={900} viewBox="0 0 560 900" style={{position: 'absolute', left: 270, top: 0,
        translate: `0px ${breathe}px`}}>
        <defs>
          <linearGradient id="robe" x1="0" x2="1">
            <stop offset="0" stopColor="#3a1f2e" /><stop offset="0.55" stopColor="#6b2f45" /><stop offset="1" stopColor="#2a1622" />
          </linearGradient>
        </defs>
        <path d="M120 360 Q280 270 440 360 L480 900 L80 900 Z" fill="url(#robe)" />
        <path d="M120 360 Q280 270 440 360" stroke="#ffb27a" strokeWidth="5" fill="none" opacity="0.7" />
        <path d="M230 318 Q280 372 330 318" stroke="#c99a5a" strokeWidth="9" fill="none" />
        <rect x="248" y="270" width="64" height="60" rx="20" fill="#2a1a24" />
        <ellipse cx="208" cy="226" rx="12" ry="20" fill="#24161f" />
        <ellipse cx="352" cy="226" rx="12" ry="20" fill="#24161f" />
        <ellipse cx="280" cy="222" rx="70" ry="82" fill="#24161f" />
        <path d="M212 210 Q216 140 280 136 Q344 140 348 210 Q330 168 280 166 Q230 168 212 210 Z" fill="#120b10" />
        <path d="M212 200 Q216 140 280 136 Q344 140 348 200" stroke="#ffb27a" strokeWidth="4" fill="none" opacity="0.8" />
        <g style={{translate: `0px ${sip}px`}}>
          <path d="M420 420 L470 330" stroke="#5a2f40" strokeWidth="44" strokeLinecap="round" />
          <rect x="452" y="282" width="38" height="52" rx="6" fill="rgba(255,235,200,0.55)" stroke="rgba(255,255,255,0.8)" strokeWidth="3" />
          <rect x="455" y="304" width="32" height="27" fill="#c98a45" opacity="0.9" />
        </g>
      </svg>
      {/* penthouse floor slab with underside lights */}
      <div style={{position: 'absolute', left: 0, top: 700, width: 1080, height: 200, background: '#15111f'}}>
        {[0, 1, 2, 3, 4, 5].map((i) => <div key={i} style={{position: 'absolute', left: 60 + i * 180, top: 150, width: 60, height: 8,
          borderRadius: 4, background: '#ffd9a0', boxShadow: '0 0 24px #ffb060'}} />)}
      </div>
    </div>
  );
};

// ------------------------------------------------------------ Tab Nagar (bottom of the world)
const COLORS = ['#2d3a5a', '#3b2e52', '#24414a', '#4a3340', '#2f4a3a', '#46402a'];
const TabBuilding: React.FC<{x: number; w: number; floors: number; seed: number}> = ({x, w, floors, seed}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{position: 'absolute', left: x, bottom: 0, width: w}}>
      {Array.from({length: floors}, (_, f) => {
        const lit = random(`l${seed}-${f}`) > 0.35;
        const flicker = random(`f${seed}-${f}-${Math.floor(frame / 9)}`) > 0.97;
        return (
          <div key={f} style={{position: 'relative', height: 74, marginTop: 6,
            background: COLORS[(seed + f) % COLORS.length], borderRadius: '18px 18px 0 0'}}>
            <div style={{position: 'absolute', left: 14, top: 12, width: 12, height: 12, borderRadius: 6,
              background: ['#f87171', '#fbbf24', '#34d399', '#60a5fa'][(seed + f) % 4]}} />
            <div style={{position: 'absolute', right: 14, top: 8, color: 'rgba(255,255,255,0.5)', fontFamily: MONO, fontSize: 18}}>×</div>
            <div style={{position: 'absolute', left: 12, right: 12, top: 32, bottom: 8, borderRadius: 6,
              background: lit && !flicker ? 'rgba(255,214,140,0.85)' : 'rgba(10,12,20,0.7)',
              fontFamily: MONO, fontSize: 16, color: '#3a2a10', display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 10}}>
              {lit && !flicker ? <>▶ 3:07</> : null}
            </div>
          </div>
        );
      })}
    </div>
  );
};

const Neon: React.FC<{text: string; x: number; y: number; color: string; seed: number}> = ({text, x, y, color, seed}) => {
  const frame = useCurrentFrame();
  const on = random(`n${seed}-${Math.floor(frame / 4)}`) > 0.06;
  return (
    <div style={{position: 'absolute', left: x, top: y, fontFamily: SANS, fontWeight: 800, fontSize: 46, letterSpacing: 4,
      color: on ? color : 'rgba(255,255,255,0.15)', textShadow: on ? `0 0 18px ${color}, 0 0 42px ${color}` : 'none',
      padding: '10px 22px', background: 'rgba(8,8,20,0.75)', borderRadius: 10}}>{text}</div>
  );
};

const Notification: React.FC<{x: number; y: number; at: number; text: string}> = ({x, y, at, text}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <div style={{position: 'absolute', left: x, top: y, fontFamily: SANS, fontWeight: 700, fontSize: 26, color: '#fff',
      background: '#e5484d', padding: '10px 18px', borderRadius: 999, whiteSpace: 'nowrap',
      opacity: interpolate(frame, [at, at + 0.2 * fps], [0, 1], clamp),
      scale: interpolate(frame, [at, at + 0.35 * fps], [0.4, 1], {...clamp, easing: Easing.spring({damping: 12}), output: 'perceptual-scale'})}}>
      {text}</div>
  );
};

const TabNagar: React.FC<{revealAt: number}> = ({revealAt}) => {
  const buildings = Array.from({length: 9}, (_, i) => ({
    x: i * 122 - 30, w: 110 + random(`bw${i}`) * 30, floors: 8 + Math.floor(random(`bf${i}`) * 9)}));
  return (
    <div style={{position: 'absolute', left: 0, top: 2000, width: 1080, height: WORLD_H - 2000,
      background: 'linear-gradient(180deg, #ffcf94 0%, #3a2a4a 18%, #12101f 60%)'}}>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 1500}}>
        {buildings.map((b, i) => <TabBuilding key={i} seed={i} {...b} />)}
      </div>
      <Neon text="TUTORIAL NAGAR" x={90} y={360} color="#22d3ee" seed={1} />
      <Neon text="NOTIFICATION CHOWK" x={330} y={560} color="#f472b6" seed={2} />
      <Neon text="DEADLINE COLONY" x={150} y={760} color="#fbbf24" seed={3} />
      <Notification x={330} y={880} at={revealAt + 10} text="🔔 New AI model beats everything" />
      <Notification x={90} y={950} at={revealAt + 22} text="You're falling behind" />
      <Notification x={560} y={1060} at={revealAt + 34} text="99+ unread" />
    </div>
  );
};

// ------------------------------------------------------------ captions (word by word)
const Captions: React.FC<{words: Word[]; offset: number}> = ({words, offset}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps - offset;
  // show the current sentence; highlight the word being spoken
  if (!words.some((w) => w.start <= t)) return null;
  let first = 0;
  words.forEach((w, i) => {
    if (i > 0 && /[.?!]$/.test(words[i - 1].text) && w.start <= t) first = i;
  });
  const rest = words.slice(first);
  const end = rest.findIndex((w) => /[.?!]$/.test(w.text));
  const shown = end === -1 ? rest : rest.slice(0, end + 1);
  return (
    <div style={{position: 'absolute', left: 80, right: 80, top: 1440, textAlign: 'center', fontFamily: SANS,
      fontWeight: 800, fontSize: 72, lineHeight: 1.12, letterSpacing: -1.5, textShadow: '0 4px 24px rgba(0,0,0,0.6)'}}>
      {shown.map((w, i) => {
        const on = w.start <= t;
        const current = on && t < w.end + 0.08;
        return (
          <span key={i} style={{color: current ? '#FFD84D' : '#FFFFFF', opacity: on ? 1 : 0, marginRight: 18,
            display: 'inline-block', scale: current ? '1.06' : '1'}}>{w.text}</span>
        );
      })}
    </div>
  );
};

const Stamp: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const text = 'PENTHOUSE · 47F · 6:12 AM';
  const n = Math.min(text.length, Math.max(0, Math.floor((frame - 0.3 * fps) / 1.5)));
  return (
    <div style={{position: 'absolute', left: 80, top: 130, fontFamily: MONO, fontWeight: 600, fontSize: 30,
      color: 'rgba(255,255,255,0.85)', letterSpacing: 2,
      opacity: interpolate(frame, [5 * fps, 5.6 * fps], [1, 0], clamp)}}>{text.slice(0, n)}</div>
  );
};

// ------------------------------------------------------------ the scene
export const Scene1: React.FC<Scene1Props> = ({line1, line2, line1Dur, line2Dur, gap, words1, words2}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tiltStart = Math.round((line1Dur - 1.6) * fps);    // "...I look down at my people"
  const tiltEnd = tiltStart + Math.round(1.8 * fps);
  const l2 = Math.round((line1Dur + gap) * fps);
  return (
    <AbsoluteFill style={{background: '#120f2e', overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: WORLD_H, transformOrigin: '50% 30%',
        translate: interpolate(frame, [tiltStart, tiltEnd], ['0px 0px', `0px ${TILT_TO}px`], {...clamp, easing: Easing.bezier(0.65, 0, 0.35, 1)}),
        scale: interpolate(frame, [0, tiltStart, tiltEnd, tiltEnd + 6 * fps], [1, 1.12, 1.02, 1.08], {...clamp, output: 'perceptual-scale'})}}>
        <Sky />
        <FarSkyline />
        <Balcony />
        <TabNagar revealAt={tiltEnd} />
      </div>
      {/* film look: soft vignette */}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)'}} />
      <Stamp />
      <Sequence durationInFrames={l2} layout="none"><Captions words={words1} offset={0} /></Sequence>
      <Sequence from={l2} layout="none"><Captions words={words2} offset={0} /></Sequence>
      <Audio name="Guru line 1" src={staticFile(line1)} />
      <Sequence from={l2} layout="none"><Audio name="Guru line 2" src={staticFile(line2)} /></Sequence>
      <Sequence from={tiltStart} layout="none"><Audio name="Whoosh" src={staticFile('sfx/whoosh.wav')} volume={0.5} /></Sequence>
      <Audio name="Ambience" src={staticFile('sfx/sunrise-pad.wav')} volume={0.35} />
    </AbsoluteFill>
  );
};
