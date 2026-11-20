// "We Ship": the ShipStack story film. Screenplay: docs/story-film.md (120 BPM, 1 beat = 15 frames).
import {loadFont} from '@remotion/fonts';
import React from 'react';
import {
  AbsoluteFill, Audio, Img, Sequence, continueRender, delayRender, interpolate, spring, staticFile,
  useCurrentFrame, useVideoConfig,
} from 'remotion';

const C = {
  bg: '#0D1117', panel: '#161B22', text: '#E6EDF3', muted: '#8B949E', accent: '#22D3EE',
  red: '#F87171', violet: '#A78BFA', green: '#34D399',
};
const SANS = 'Geist, sans-serif';
const MONO = '"Geist Mono", monospace';

const fontsReady = delayRender('fonts');
Promise.all([
  loadFont({family: 'Geist', url: staticFile('fonts/Geist-Variable.ttf'), weight: '100 900'}),
  loadFont({family: 'Geist Mono', url: staticFile('fonts/GeistMono-Variable.ttf'), weight: '100 900'}),
]).then(() => continueRender(fontsReady));

// One spring for every entrance: settles in ~0.5 s, overshoots once at most.
const useEnter = (delay = 0, stiff = 140) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - delay, fps, config: {damping: 16, stiffness: stiff, mass: 0.7}});
};

const Rise: React.FC<{delay?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({delay = 0, children, style}) => {
  const p = useEnter(delay);
  return (
    <div style={{opacity: p, transform: `translateY(${(1 - p) * 24}px)`, ...style}}>{children}</div>
  );
};

const Cursor: React.FC<{color?: string; h?: number}> = ({color = C.accent, h = 60}) => {
  const frame = useCurrentFrame();
  return <span style={{display: 'inline-block', width: h * 0.55, height: h * 0.12, background: color,
    marginLeft: 8, opacity: Math.floor(frame / 15) % 2 === 0 ? 1 : 0.15}} />;
};

// The Bracket Boat mark (same geometry as reels/shipstack/studio/theme.py: draw_boat)
const Boat: React.FC<{size: number; sail?: number; hull?: number}> = ({size, sail = 1, hull = 1}) => (
  <svg width={size} height={size} viewBox="0 0 10 10">
    <g style={{opacity: hull, transform: `translateY(${(1 - hull) * 1.5}px)`}}>
      <polygon points="1.9,6.15 8.1,6.15 6.85,7.9 3.15,7.9" fill={C.accent} />
    </g>
    <g style={{opacity: sail, transform: `translateX(${(1 - sail) * -2.5}px)`}}>
      <polygon points="3.5,2 4.9375,2 6.9,3.75 4.9375,5.5 3.5,5.5 5.4625,3.75" fill={C.accent} />
    </g>
  </svg>
);

const Typed: React.FC<{text: string; start: number; every?: number}> = ({text, start, every = 2}) => {
  const frame = useCurrentFrame();
  const n = Math.max(0, Math.min(text.length, Math.floor((frame - start) / every)));
  return <>{text.slice(0, n)}</>;
};

// ---------------------------------------------------------------- scenes
const Terminal: React.FC = () => {
  const frame = useCurrentFrame();
  const err = useEnter(45, 220);
  return (
    <AbsoluteFill style={{justifyContent: 'center', padding: '0 80px', fontFamily: MONO, fontSize: 56, color: C.text}}>
      <div>
        <span style={{color: C.muted}}>$ </span>
        <Typed text="ship my-idea" start={6} />
        {frame < 45 && <Cursor color={C.text} h={60} />}
      </div>
      <div style={{color: C.red, marginTop: 28, opacity: err, transform: `translateX(${(1 - err) * 8}px)`}}>
        error: where do I even start?
      </div>
    </AbsoluteFill>
  );
};

const Words: React.FC = () => (
  <AbsoluteFill style={{justifyContent: 'center', padding: '0 80px', fontFamily: SANS, fontWeight: 800,
    fontSize: 168, lineHeight: 1.02, letterSpacing: -6, color: C.text}}>
    <Rise delay={0}>Learn it.</Rise>
    <Rise delay={15}>Build it.</Rise>
    <Rise delay={30} style={{color: C.accent}}>Ship it.</Rise>
  </AbsoluteFill>
);

const Logo: React.FC = () => {
  const hull = useEnter(0, 120);
  const sail = useEnter(10, 260);
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      <Boat size={420} hull={hull} sail={sail} />
      <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 132, letterSpacing: -5, color: C.text, marginTop: 10,
        height: 160, display: 'flex', alignItems: 'flex-end'}}>
        <Typed text="shipstack" start={20} every={2} />
        <Cursor h={132} />
      </div>
    </AbsoluteFill>
  );
};

const Series: React.FC<{label: string; color: string; title: React.ReactNode; card: string; width: number;
  children?: React.ReactNode}> = ({label, color, title, card, width, children}) => {
  const p = useEnter(4, 110);
  return (
    <AbsoluteFill style={{padding: '220px 80px 0', fontFamily: SANS}}>
      <Rise><div style={{fontFamily: MONO, fontWeight: 700, fontSize: 34, color, letterSpacing: 2}}>{label}</div></Rise>
      <Rise delay={2}>
        <div style={{fontWeight: 800, fontSize: 84, lineHeight: 1.05, letterSpacing: -3, color: C.text, marginTop: 18}}>{title}</div>
      </Rise>
      <div style={{position: 'absolute', left: (1080 - width) / 2, top: 600, width, opacity: p,
        transform: `translateY(${(1 - p) * 120}px) scale(${0.94 + 0.06 * p})`, transformOrigin: 'top center'}}>
        <Img src={staticFile(card)} style={{width, borderRadius: 28, display: 'block'}} />
        {children}
      </div>
    </AbsoluteFill>
  );
};

const Counter: React.FC = () => {
  const frame = useCurrentFrame();
  const n = Math.round(interpolate(frame, [8, 52], [1, 1200], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: (t) => 1 - Math.pow(1 - t, 3)}));
  return (
    <div style={{position: 'absolute', right: -24, top: -36, background: C.accent, color: C.bg, fontFamily: MONO,
      fontWeight: 800, fontSize: 56, padding: '10px 22px', borderRadius: 18}}>#{String(n).padStart(4, '0')}</div>
  );
};

const End: React.FC = () => (
  <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', fontFamily: SANS}}>
    <Rise><Boat size={300} /></Rise>
    <div style={{display: 'flex', gap: 28, fontWeight: 800, fontSize: 104, letterSpacing: -4, color: C.text, marginTop: 30}}>
      <Rise delay={0}>Know.</Rise>
      <Rise delay={15}>Save.</Rise>
      <Rise delay={30} style={{color: C.accent}}>Ship.</Rise>
    </div>
    <Rise delay={45}>
      <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 44, color: C.muted, marginTop: 40}}>
        Follow <span style={{color: C.text}}>@shipstack_</span>
      </div>
    </Rise>
  </AbsoluteFill>
);

export const Story: React.FC = () => (
  <AbsoluteFill style={{background: C.bg}}>
    <Audio src={staticFile('bgm.wav')} />
    <Sequence durationInFrames={60}><Terminal /></Sequence>
    <Sequence from={60} durationInFrames={45}><Words /></Sequence>
    <Sequence from={105} durationInFrames={75}><Logo /></Sequence>
    <Sequence from={180} durationInFrames={65}>
      <Series label="NEWS" color={C.red} card="cards/news-sample.png" width={760}
        title={<>AI news. <span style={{color: C.accent}}>Verified.</span><br />Every source shown.</>} />
    </Sequence>
    <Sequence from={245} durationInFrames={65}>
      <Series label="AI AUTOMATION" color={C.violet} card="cards/automation-sample.png" width={760}
        title={<>Automations<br />you can <span style={{color: C.accent}}>copy.</span></>} />
    </Sequence>
    <Sequence from={310} durationInFrames={65}>
      <Series label="DSA" color={C.green} card="cards/dsa-sample.png" width={540}
        title={<><span style={{color: C.accent}}>1,200</span> DSA problems.<br />Debugged line by line.</>}>
        <Counter />
      </Series>
    </Sequence>
    <Sequence from={375} durationInFrames={75}><End /></Sequence>
  </AbsoluteFill>
);
