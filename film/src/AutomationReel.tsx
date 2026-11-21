// Text-only automation reel (15 s, 30 fps, 1080x1920). Everything is typed: hook, trigger, each step, result.
// Same dark Studio look as the news cards and DSA debugger. Data: automation-data.json (or props).
// Remotion rules (remotion-dev/skills): inline interpolate()/Easing, no CSS transitions, individual
// translate/scale, fonts via @remotion/fonts, 80 px side / 100 px top-bottom safe area.
import {loadFont} from '@remotion/fonts';
import {Audio} from '@remotion/media';
import React from 'react';
import {AbsoluteFill, Easing, Sequence, continueRender, delayRender, interpolate, staticFile, useCurrentFrame} from 'remotion';
import defaults from './automation-data.json';

const C = {bg: '#0D1117', panel: '#161B22', line: '#2A313C', text: '#E6EDF3', muted: '#8B949E', accent: '#22D3EE', ok: '#3FB950'};
const SANS = 'Geist, sans-serif';
const MONO = '"Geist Mono", monospace';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ease = Easing.bezier(0.16, 1, 0.3, 1);
const FPS = 30;
const T = {hook: 0.3, trig: 3.0, step0: 4.6, stepEvery: 1.85, result: 12.0, cta: 13.4};

const ready = delayRender('Loading Geist');
Promise.all([
  loadFont({family: 'Geist', url: staticFile('fonts/Geist-Variable.ttf'), weight: '100 900'}),
  loadFont({family: 'Geist Mono', url: staticFile('fonts/GeistMono-Variable.ttf'), weight: '100 900'}),
]).then(() => continueRender(ready));

export type AutomationProps = typeof defaults;

// How many characters of `text` are visible at `frame` when typing starts at `startSec` (cps = chars/second).
const typedCount = (frame: number, startSec: number, text: string, cps = 22) =>
  Math.max(0, Math.min(text.length, Math.floor((frame - startSec * FPS) * cps / FPS) + 1));

// Frames on which a key sound should play for a given typed line.
const keyFrames = (startSec: number, text: string, cps = 22) => {
  const out: number[] = [];
  for (let i = 0; i < text.length; i++) if (text[i] !== ' ') out.push(Math.round(startSec * FPS + i * FPS / cps));
  return out;
};

const Cursor: React.FC<{h: number; w?: number; active?: boolean}> = ({h, w = 0.55, active = true}) => {
  const frame = useCurrentFrame();
  const on = !active || Math.floor(frame / 15) % 2 === 0;
  return <span style={{display: 'inline-block', width: h * w * 0.5, height: h * 0.9, marginLeft: 8, background: C.accent,
    opacity: on ? 1 : 0, verticalAlign: 'text-bottom'}} />;
};

export const AutomationReel: React.FC<Partial<AutomationProps>> = (p) => {
  const d = {...defaults, ...p} as AutomationProps;
  const frame = useCurrentFrame();
  const sec = frame / FPS;

  // ---- hook (types, then lifts to the top and shrinks)
  const hookN = typedCount(frame, T.hook, d.hook, 20);
  const lift = interpolate(sec, [2.6, 3.4], [0, 1], {...clamp, easing: ease});
  const hookShown = d.hook.slice(0, hookN);
  const [pre, post] = hookShown.includes(d.accentWord) || d.hook.startsWith(d.accentWord)
    ? [null, null] : [null, null];
  const renderHook = () => {
    const i = d.hook.indexOf(d.accentWord), j = i + d.accentWord.length;
    const a = hookShown.slice(0, i), b = hookShown.slice(i, j), c = hookShown.slice(j);
    return <>{a}<span style={{color: C.accent}}>{b}</span>{c}</>;
  };
  void pre; void post;

  // ---- trigger line
  const trigText = d.trigger;
  const trigN = typedCount(frame, T.trig, trigText, 26);

  // ---- steps
  const stepStart = (i: number) => T.step0 + i * T.stepEvery;
  const stepsGeom = {top: 690, gap: 218, x: 80, w: 920, h: 168};

  // ---- result
  const res = interpolate(sec, [T.result, T.result + 0.35], [0, 1], {...clamp, easing: ease});
  const progress = interpolate(sec, [T.result + 0.3, T.result + 1.3], [0, 1], {...clamp, easing: Easing.bezier(0.65, 0, 0.35, 1)});

  // ---- keyboard sounds: one short click per typed character
  const keys: number[] = [
    ...keyFrames(T.hook, d.hook, 20), ...keyFrames(T.trig, trigText, 26),
    ...d.steps.flatMap((s, i) => keyFrames(stepStart(i) + 0.25, s.text, 28)),
    ...keyFrames(T.cta, d.cta, 30),
  ];

  const ctaN = typedCount(frame, T.cta, d.cta, 30);

  return (
    <AbsoluteFill style={{background: C.bg, color: C.text, fontFamily: SANS, overflow: 'hidden'}}>
      {/* faint grid so the page never feels empty */}
      <AbsoluteFill style={{backgroundImage: `linear-gradient(${C.line}33 1px, transparent 1px), linear-gradient(90deg, ${C.line}33 1px, transparent 1px)`,
        backgroundSize: '90px 90px', opacity: 0.5}} />

      {/* header: category + tool */}
      <div style={{position: 'absolute', left: 80, right: 80, top: 100, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        fontFamily: MONO, fontSize: 28, letterSpacing: 3, color: C.muted, opacity: interpolate(sec, [0, 0.4], [0, 1], clamp)}}>
        <span style={{color: C.accent}}>AI AUTOMATION</span><span>{d.tool}</span>
      </div>

      {/* hook */}
      <div style={{position: 'absolute', left: 80, right: 80, top: interpolate(lift, [0, 1], [640, 190]),
        fontWeight: 800, letterSpacing: -3, lineHeight: 1.04,
        fontSize: interpolate(lift, [0, 1], [128, 84])}}>
        {renderHook()}{hookN < d.hook.length || lift < 1 ? <Cursor h={interpolate(lift, [0, 1], [128, 84])} /> : null}
      </div>

      {/* trigger */}
      <div style={{position: 'absolute', left: 80, right: 80, top: 470, opacity: interpolate(sec, [T.trig - 0.1, T.trig + 0.2], [0, 1], clamp),
        fontFamily: MONO, fontSize: 40, color: C.text, background: C.panel, border: `2px solid ${C.line}`, borderRadius: 20,
        padding: '30px 36px', translate: `0px ${interpolate(sec, [T.trig - 0.1, T.trig + 0.4], [24, 0], {...clamp, easing: ease})}px`}}>
        <span style={{color: C.accent}}>when </span>{trigText.slice(0, trigN)}
        {trigN < trigText.length ? <Cursor h={40} /> : <span style={{color: C.muted}}> →</span>}
      </div>

      {/* steps */}
      {d.steps.map((s, i) => {
        const t0 = stepStart(i);
        const appear = interpolate(sec, [t0, t0 + 0.45], [0, 1], {...clamp, easing: ease});
        const n = typedCount(frame, t0 + 0.25, s.text, 28);
        const done = t0 + 0.25 + s.text.length / 28 + 0.12;
        const pop = interpolate(sec, [done, done + 0.35], [0, 1], {...clamp, easing: Easing.out(Easing.back(2.2))});
        const ring = interpolate(sec, [done, done + 0.6], [0, 1], clamp);
        const y = stepsGeom.top + i * stepsGeom.gap;
        const lineIn = interpolate(sec, [t0 - 0.45, t0], [0, 1], {...clamp, easing: Easing.bezier(0.65, 0, 0.35, 1)});
        return (
          <React.Fragment key={i}>
            {i > 0 || true ? (
              <div style={{position: 'absolute', left: 150, top: y - 56 - (i === 0 ? 0 : 0), width: 6, height: 56 * (i === 0 ? 0 : lineIn),
                background: C.accent, borderRadius: 3}} />
            ) : null}
            <div style={{position: 'absolute', left: stepsGeom.x, top: y, width: stepsGeom.w, height: stepsGeom.h, opacity: appear,
              translate: `${interpolate(appear, [0, 1], [-60, 0])}px 0px`, background: C.panel, border: `2px solid ${pop > 0.5 ? C.ok + '99' : C.line}`,
              borderRadius: 28, display: 'flex', alignItems: 'center', padding: '0 36px', gap: 32}}>
              <div style={{width: 76, height: 76, borderRadius: 38, background: pop > 0.5 ? C.ok : C.bg, border: `3px solid ${pop > 0.5 ? C.ok : C.accent}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: MONO, fontWeight: 800, fontSize: 36,
                color: pop > 0.5 ? C.bg : C.accent, flex: 'none', scale: `${interpolate(pop, [0, 1], [1, 1.12])}`}}>
                {pop > 0.5 ? '✓' : i + 1}
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 6, minWidth: 0}}>
                <div style={{fontFamily: MONO, fontSize: 28, letterSpacing: 2, color: C.accent}}>{s.app.toUpperCase()}</div>
                <div style={{fontSize: 44, fontWeight: 700, letterSpacing: -1, whiteSpace: 'nowrap'}}>
                  {s.text.slice(0, n)}{n < s.text.length ? <Cursor h={44} /> : null}
                </div>
              </div>
              <div style={{position: 'absolute', right: 28, top: '50%', width: 60, height: 60, marginTop: -30, borderRadius: 30,
                border: `3px solid ${C.ok}`, opacity: (1 - ring) * (ring > 0 ? 1 : 0), scale: `${1 + ring * 1.2}`}} />
            </div>
          </React.Fragment>
        );
      })}

      {/* result */}
      <div style={{position: 'absolute', left: 80, right: 80, top: 1640, opacity: res, translate: `0px ${(1 - res) * 30}px`,
        display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', fontFamily: MONO, fontWeight: 700}}>
        <span style={{fontSize: 40, color: C.muted, textDecoration: progress > 0.5 ? 'line-through' : 'none'}}>{d.resultFrom}</span>
        <span style={{fontSize: 44, color: C.accent}}>→</span>
        <span style={{fontSize: 84, color: C.ok, letterSpacing: -2}}>{d.resultTo}</span>
      </div>

      {/* cta + handle */}
      <div style={{position: 'absolute', left: 80, right: 80, top: 1810, fontFamily: MONO, fontSize: 30, color: C.muted, letterSpacing: 1,
        display: 'flex', justifyContent: 'space-between'}}>
        <span>{d.cta.slice(0, ctaN)}</span><span style={{color: C.accent, opacity: sec > T.cta ? 1 : 0}}>@shipstack_</span>
      </div>

      {keys.map((k, i) => (
        <Sequence key={i} from={k} durationInFrames={6} layout="none">
          <Audio src={staticFile(`sfx/key${i % 3}.wav`)} volume={0.55 + (i % 5) * 0.06} />
        </Sequence>
      ))}
      {d.steps.map((_, i) => {
        const done = stepStart(i) + 0.25 + d.steps[i].text.length / 28 + 0.12;
        return <Sequence key={`d${i}`} from={Math.round(done * FPS)} durationInFrames={12} layout="none"><Audio src={staticFile('sfx/done.wav')} volume={0.5} /></Sequence>;
      })}
      <Sequence from={Math.round(T.result * FPS)} durationInFrames={30} layout="none"><Audio src={staticFile('sfx/result.wav')} volume={0.7} /></Sequence>
    </AbsoluteFill>
  );
};
