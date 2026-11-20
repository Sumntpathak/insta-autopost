// "We Ship": the ShipStack story film. Screenplay: docs/story-film.md (120 BPM: 1 beat = fps / 2).
// Follows the Remotion agent skills (github.com/remotion-dev/skills): inline interpolate() with
// Easing.spring / Easing.bezier, individual `translate` / `scale` properties, perceptual scale,
// timing from useVideoConfig().fps, TransitionSeries for consecutive scenes, Audio from @remotion/media,
// local fonts via @remotion/fonts, 80 px side / 100 px top-bottom safe area, headlines >= 84 px.
import {loadFont} from '@remotion/fonts';
import {Audio} from '@remotion/media';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import type {TransitionPresentationComponentProps} from '@remotion/transitions';
import React from 'react';
import {
  AbsoluteFill, Easing, Img, continueRender, delayRender, interpolate, staticFile, useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const C = {
  bg: '#0D1117', panel: '#161B22', text: '#E6EDF3', muted: '#8B949E', accent: '#22D3EE',
  red: '#F87171', violet: '#A78BFA', green: '#34D399',
};
const SANS = 'Geist, sans-serif';
const MONO = '"Geist Mono", monospace';
const SAFE = {left: 80, right: 80, top: 100, bottom: 100};
const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const fontsReady = delayRender('Loading Geist');
Promise.all([
  loadFont({family: 'Geist', url: staticFile('fonts/Geist-Variable.ttf'), weight: '100 900'}),
  loadFont({family: 'Geist Mono', url: staticFile('fonts/GeistMono-Variable.ttf'), weight: '100 900'}),
]).then(() => continueRender(fontsReady));

// --------------------------------------------------------------- small, frame-subscribed pieces
const Rise: React.FC<{beat?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({beat = 0, children, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const start = (beat * fps) / 2;
  return (
    <div style={{
      opacity: interpolate(frame, [start, start + 0.35 * fps], [0, 1], {...clamp, easing: EASE_OUT}),
      translate: interpolate(frame, [start, start + 0.5 * fps], ['0px 28px', '0px 0px'], {...clamp, easing: Easing.spring({damping: 200})}),
      ...style,
    }}>{children}</div>
  );
};

const Cursor: React.FC<{color?: string; size: number}> = ({color = C.accent, size}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return <span style={{display: 'inline-block', width: size * 0.55, height: size * 0.12, background: color, marginLeft: 8,
    opacity: Math.floor(frame / (fps / 2)) % 2 === 0 ? 1 : 0.15}} />;
};

const Typed: React.FC<{text: string; startSec: number; perChar?: number}> = ({text, startSec, perChar = 2}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const n = Math.max(0, Math.min(text.length, Math.floor((frame - startSec * fps) / perChar)));
  return <>{text.slice(0, n)}</>;
};

// The Bracket Boat mark (same geometry as reels/shipstack/studio/theme.py: draw_boat)
const Boat: React.FC<{size: number; animate?: boolean}> = ({size, animate = false}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const hull = animate ? interpolate(frame, [0, 0.5 * fps], [0, 1], {...clamp, easing: Easing.spring({damping: 14})}) : 1;
  const sail = animate ? interpolate(frame, [0.33 * fps, 0.6 * fps], [0, 1], {...clamp, easing: Easing.spring({damping: 12})}) : 1;
  return (
    <svg width={size} height={size} viewBox="0 0 10 10" style={{overflow: 'visible'}}>
      <polygon points="1.9,6.15 8.1,6.15 6.85,7.9 3.15,7.9" fill={C.accent}
        style={{opacity: Math.min(1, hull * 1.5), translate: `0px ${(1 - hull) * 1.6}px`}} />
      <polygon points="3.5,2 4.9375,2 6.9,3.75 4.9375,5.5 3.5,5.5 5.4625,3.75" fill={C.accent}
        style={{opacity: Math.min(1, sail * 1.5), translate: `${(1 - sail) * -2.6}px 0px`}} />
    </svg>
  );
};

// --------------------------------------------------------------- scenes
const Terminal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{justifyContent: 'center', paddingLeft: SAFE.left, paddingRight: SAFE.right,
      fontFamily: MONO, fontSize: 60, color: C.text}}>
      <div>
        <span style={{color: C.muted}}>$ </span>
        <Typed text="ship my-idea" startSec={0.2} />
        {frame < 1.5 * fps && <Cursor color={C.text} size={60} />}
      </div>
      <div style={{color: C.red, marginTop: 32,
        opacity: interpolate(frame, [1.5 * fps, 1.6 * fps], [0, 1], clamp),
        translate: interpolate(frame, [1.5 * fps, 1.6 * fps, 1.7 * fps, 1.8 * fps], ['10px 0px', '-6px 0px', '3px 0px', '0px 0px'], clamp)}}>
        error: where do I start?
      </div>
    </AbsoluteFill>
  );
};

const Words: React.FC = () => (
  <AbsoluteFill style={{justifyContent: 'center', paddingLeft: SAFE.left, fontFamily: SANS, fontWeight: 800,
    fontSize: 176, lineHeight: 1.0, letterSpacing: -7, color: C.text}}>
    <Rise beat={0}>Learn it.</Rise>
    <Rise beat={1}>Build it.</Rise>
    <Rise beat={2} style={{color: C.accent}}>Ship it.</Rise>
  </AbsoluteFill>
);

const Logo: React.FC = () => (
  <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
    <Boat size={440} animate />
    <div style={{fontFamily: SANS, fontWeight: 800, fontSize: 136, letterSpacing: -5, color: C.text,
      height: 170, display: 'flex', alignItems: 'flex-end'}}>
      <Typed text="shipstack" startSec={0.66} />
      <Cursor size={136} />
    </div>
  </AbsoluteFill>
);

const Card: React.FC<{src: string; width: number; children?: React.ReactNode}> = ({src, width, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <div style={{position: 'absolute', left: (1080 - width) / 2, top: 640, width,
      opacity: interpolate(frame, [0.1 * fps, 0.4 * fps], [0, 1], {...clamp, easing: EASE_OUT}),
      translate: interpolate(frame, [0.1 * fps, 0.7 * fps], ['0px 140px', '0px 0px'], {...clamp, easing: Easing.spring({damping: 200})}),
      scale: interpolate(frame, [0.1 * fps, 0.7 * fps], [0.92, 1], {...clamp, easing: EASE_OUT, output: 'perceptual-scale'})}}>
      <Img src={staticFile(src)} style={{width, borderRadius: 32, display: 'block'}} />
      {children}
    </div>
  );
};

const Series: React.FC<{label: string; color: string; title: React.ReactNode; card: string; width: number;
  children?: React.ReactNode}> = ({label, color, title, card, width, children}) => (
  <AbsoluteFill style={{background: C.bg, paddingTop: 200, paddingLeft: SAFE.left, paddingRight: SAFE.right, fontFamily: SANS}}>
    <Rise><div style={{fontFamily: MONO, fontWeight: 700, fontSize: 44, color, letterSpacing: 3}}>{label}</div></Rise>
    <Rise>
      <div style={{fontWeight: 800, fontSize: 88, lineHeight: 1.04, letterSpacing: -3, color: C.text, marginTop: 20}}>{title}</div>
    </Rise>
    <Card src={card} width={width}>{children}</Card>
  </AbsoluteFill>
);

const Counter: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const n = Math.round(interpolate(frame, [0.3 * fps, 1.8 * fps], [1, 1200], {...clamp, easing: EASE_OUT}));
  return (
    <div style={{position: 'absolute', right: -28, top: -40, background: C.accent, color: C.bg, fontFamily: MONO,
      fontWeight: 800, fontSize: 60, padding: '10px 24px', borderRadius: 20}}>#{String(n).padStart(4, '0')}</div>
  );
};

const End: React.FC = () => (
  <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', fontFamily: SANS}}>
    <Rise><Boat size={320} /></Rise>
    <div style={{display: 'flex', gap: 28, fontWeight: 800, fontSize: 108, letterSpacing: -4, color: C.text, marginTop: 24}}>
      <Rise beat={0}>Know.</Rise>
      <Rise beat={1}>Save.</Rise>
      <Rise beat={2} style={{color: C.accent}}>Ship.</Rise>
    </div>
    <Rise beat={3}>
      <div style={{fontFamily: MONO, fontWeight: 600, fontSize: 48, color: C.muted, marginTop: 44}}>
        Follow <span style={{color: C.text}}>@shipstack_</span>
      </div>
    </Rise>
  </AbsoluteFill>
);

// Custom presentation: the next series slides up over the previous one (no fade, no blur).
const SlideUp = ({children, presentationDirection, presentationProgress}: TransitionPresentationComponentProps<Record<string, never>>) => {
  if (presentationDirection === 'exiting') {
    return <AbsoluteFill style={{translate: `0px ${-presentationProgress * 12}%`}}>{children}</AbsoluteFill>;
  }
  return <AbsoluteFill style={{translate: `0px ${(1 - presentationProgress) * 100}%`}}>{children}</AbsoluteFill>;
};
const slideUp = {component: SlideUp, props: {}};

// --------------------------------------------------------------- the film (exactly 15 s)
export const Story: React.FC = () => {
  const {fps} = useVideoConfig();
  const beat = fps / 2;                // 120 BPM
  const T = Math.round(fps / 3);               // slide transition; scene lengths include it so cuts stay on the beat
  const transition = <TransitionSeries.Transition presentation={slideUp}
    timing={linearTiming({durationInFrames: T, easing: Easing.bezier(0.65, 0, 0.35, 1)})} />;
  return (
    <AbsoluteFill style={{background: C.bg}}>
      <Audio name="Score" src={staticFile('bgm.wav')} />
      <TransitionSeries>
        <TransitionSeries.Sequence name="Cold open" durationInFrames={4 * beat}><Terminal /></TransitionSeries.Sequence>
        <TransitionSeries.Sequence name="Learn Build Ship" durationInFrames={3 * beat}><Words /></TransitionSeries.Sequence>
        <TransitionSeries.Sequence name="Logo" durationInFrames={5 * beat}><Logo /></TransitionSeries.Sequence>
        <TransitionSeries.Sequence name="News" durationInFrames={65 + T}>
          <Series label="NEWS" color={C.red} card="cards/news-sample.png" width={740}
            title={<>AI news. <span style={{color: C.accent}}>Verified.</span><br />Every source shown.</>} />
        </TransitionSeries.Sequence>
        {transition}
        <TransitionSeries.Sequence name="AI Automation" durationInFrames={65 + T}>
          <Series label="AI AUTOMATION" color={C.violet} card="cards/automation-sample.png" width={740}
            title={<>Automations<br />you can <span style={{color: C.accent}}>copy.</span></>} />
        </TransitionSeries.Sequence>
        {transition}
        <TransitionSeries.Sequence name="DSA" durationInFrames={65}>
          <Series label="DSA" color={C.green} card="cards/dsa-sample.png" width={520}
            title={<><span style={{color: C.accent}}>1,200</span> DSA problems.<br />Debugged line by line.</>}>
            <Counter />
          </Series>
        </TransitionSeries.Sequence>
        <TransitionSeries.Sequence name="End card" durationInFrames={5 * beat}><End /></TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
