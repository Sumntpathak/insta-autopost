import {AbsoluteFill, Easing, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, DOCTOR, NAME, SANS, SERIF} from './brand';
import {Logo} from './Logo';

export const FPS = 30;
const s = (x: number) => Math.round(x * FPS);
export const TOTAL = s(30);

// trailer seconds -> source footage seconds
const CUTS = [
  {at: 0, len: 20, src: 0},
  {at: 20, len: 3, src: 92},
  {at: 23, len: 3, src: 122},
  {at: 26, len: 4, src: 205},
];

const ease = Easing.bezier(0.22, 1, 0.36, 1);
const tween = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, b], [from, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
const useIn = (start: number, end: number) => {
  const f = useCurrentFrame();
  return Math.min(tween(f, s(start), s(start + 0.5)), tween(f, s(end - 0.4), s(end), 1, 0));
};

const Footage = ({src, shrink = 0}: {src: number; shrink?: number}) => {
  const f = useCurrentFrame();
  const push = 1 + f * 0.00012; // slow push-in
  const w = 1920 - shrink * (1920 - 760), h = 1080 - shrink * (1080 - 428);
  const x = shrink * 90, y = shrink * 330;
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, overflow: 'hidden', borderRadius: shrink * 28,
      boxShadow: shrink ? '0 20px 60px rgba(0,0,0,.45)' : undefined}}>
      <div style={{width: '100%', height: '100%', transform: `scale(${push})`}}>
        <OffthreadVideo src={staticFile('footage.mp4')} startFrom={s(src)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </div>
    </div>
  );
};

const Tag = ({children, color, style}: {children: React.ReactNode; color: string; style?: React.CSSProperties}) => (
  <div style={{background: color, color: '#fff', fontFamily: SANS, fontWeight: 800, fontSize: 44, padding: '18px 34px', borderRadius: 18,
    boxShadow: '0 10px 30px rgba(0,0,0,.35)', letterSpacing: 1, ...style}}>{children}</div>
);

const Sting = () => {
  const f = useCurrentFrame();
  const wipe = tween(f, s(2.1), s(2.9), 0, 100);
  const logoT = tween(f, 4, s(1.2));
  const text = tween(f, s(1.1), s(1.7));
  return (
    <AbsoluteFill style={{background: `linear-gradient(135deg, ${C.maroon}, ${C.maroonDark})`, transform: `translateX(${wipe}%)`,
      alignItems: 'center', justifyContent: 'center'}}>
      <div style={{transform: `translateX(${-wipe * 0.4}%)`, textAlign: 'center'}}>
        <Logo size={260} t={logoT} dark />
        <div style={{fontFamily: SERIF, color: C.cream, fontSize: 84, fontWeight: 700, marginTop: 18, opacity: text, transform: `translateY(${(1 - text) * 24}px)`}}>
          {NAME}
        </div>
        <div style={{fontFamily: SANS, color: C.teal, fontSize: 30, letterSpacing: 8, marginTop: 10, opacity: text}}>CARING SMILES · TRUSTED CARE</div>
      </div>
    </AbsoluteFill>
  );
};

const LowerThird = () => {
  const o = useIn(3.2, 8);
  const f = useCurrentFrame();
  const bar = tween(f, s(3.2), s(3.8));
  return (
    <div style={{position: 'absolute', left: 80, bottom: 90, opacity: o, transform: `translateX(${(1 - o) * -60}px)`}}>
      <div style={{display: 'flex', background: C.cream, borderRadius: 14, overflow: 'hidden', boxShadow: '0 12px 36px rgba(0,0,0,.4)'}}>
        <div style={{width: 14, background: C.maroon, height: '100%'}} />
        <div style={{padding: '18px 36px 18px 26px'}}>
          <div style={{fontFamily: SERIF, fontSize: 56, fontWeight: 700, color: C.maroon}}>{DOCTOR}</div>
          <div style={{fontFamily: SANS, fontSize: 28, color: C.ink, marginTop: 4}}>Dental Surgeon · {NAME}</div>
        </div>
      </div>
      <div style={{height: 5, width: `${bar * 100}%`, background: C.teal, marginTop: 8, borderRadius: 3}} />
    </div>
  );
};

const TitleCard = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = f - s(8);
  const sp = (d: number) => spring({frame: a - d, fps, config: {damping: 14}});
  const shrink = tween(f, s(14.5), s(15.3));
  const o = tween(f, s(8), s(8.4)) ;
  return (
    <>
      {/* big title -> collapses to corner chapter tag */}
      <div style={{position: 'absolute', left: 960 - shrink * 900, top: 70 - shrink * 30, opacity: o, width: 'max-content',
        transform: `translateX(${-50 * (1 - shrink)}%) scale(${1 - shrink * 0.5})`, transformOrigin: 'top left'}}>
        <span style={{display: 'inline-block', background: C.cream, color: C.maroon, fontFamily: SERIF, fontWeight: 700, fontSize: 70,
          padding: '14px 46px', borderRadius: 22, boxShadow: '0 12px 36px rgba(0,0,0,.4)'}}>Normal vs Cancerous Ulcer</span>
      </div>
      <div style={{opacity: 1 - shrink}}>
        <div style={{position: 'absolute', left: 90, top: 440, transform: `translateX(${(1 - sp(6)) * -500}px)`}}>
          <Tag color={C.teal}>✓ NORMAL</Tag>
          <div style={{fontFamily: SANS, color: '#fff', fontSize: 30, marginTop: 12, textShadow: '0 2px 8px #000'}}>Heals on its own</div>
        </div>
        <div style={{position: 'absolute', right: 90, top: 440, textAlign: 'right', transform: `translateX(${(1 - sp(12)) * 500}px)`}}>
          <Tag color={C.red}>! CANCEROUS</Tag>
          <div style={{fontFamily: SANS, color: '#fff', fontSize: 30, marginTop: 12, textShadow: '0 2px 8px #000'}}>Needs a quick check</div>
        </div>
        <div style={{position: 'absolute', left: 900, top: 470, width: 120, height: 120, borderRadius: 60, background: C.maroon, color: C.cream,
          fontFamily: SERIF, fontSize: 52, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center',
          transform: `scale(${sp(18)})`, border: `5px solid ${C.cream}`}}>VS</div>
      </div>
    </>
  );
};

const Causes = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = f - s(20);
  const items = ['Fever', 'Low water intake', 'Poor diet'];
  const out = tween(f, s(22.6), s(23), 1, 0);
  if (f < s(20) || f > s(23)) return null;
  return (
    <div style={{opacity: out}}>
      <div style={{position: 'absolute', left: 80, top: 160, fontFamily: SERIF, fontSize: 64, fontWeight: 700, color: C.cream, textShadow: '0 3px 12px #000'}}>
        Common causes
      </div>
      {items.map((t, i) => {
        const sp = spring({frame: a - 8 - i * 9, fps, config: {damping: 13}});
        return (
          <div key={t} style={{position: 'absolute', left: 80, top: 270 + i * 112, transform: `translateX(${(1 - sp) * -520}px)`}}>
            <Tag color={C.maroon} style={{display: 'flex', alignItems: 'center', gap: 20}}>
              <span style={{width: 16, height: 16, borderRadius: 8, background: C.teal}} />{t}
            </Tag>
          </div>
        );
      })}
    </div>
  );
};

const Heal = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = f - s(23);
  const sp = spring({frame: a, fps, config: {damping: 12}});
  const out = tween(f, s(25.6), s(26), 1, 0);
  if (f < s(23) || f > s(26)) return null;
  const day = Math.min(4, 1 + Math.floor(tween(f, s(23.5), s(25.2)) * 3.999));
  return (
    <div style={{position: 'absolute', right: 90, top: 250, textAlign: 'center', opacity: out, transform: `scale(${sp})`}}>
      <div style={{background: C.cream, borderRadius: 30, padding: '30px 60px', boxShadow: '0 16px 44px rgba(0,0,0,.45)', borderBottom: `10px solid ${C.teal}`}}>
        <div style={{fontFamily: SANS, color: C.brown, fontSize: 30, letterSpacing: 4, fontWeight: 700}}>NORMAL ULCER HEALS IN</div>
        <div style={{fontFamily: SERIF, color: C.maroon, fontSize: 150, fontWeight: 700, lineHeight: 1.1}}>3–4 <span style={{fontSize: 70}}>days</span></div>
        <div style={{display: 'flex', gap: 14, justifyContent: 'center', marginTop: 8}}>
          {[1, 2, 3, 4].map((d) => <div key={d} style={{width: 54, height: 12, borderRadius: 6, background: d <= day ? C.teal : '#d8cfc3'}} />)}
        </div>
      </div>
    </div>
  );
};

const EndCard = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = f - s(26);
  const bg = tween(f, s(26), s(26.6));
  const sp = (d: number) => spring({frame: a - d, fps, config: {damping: 14}});
  const pulse = 1 + 0.05 * Math.sin(Math.max(0, a - 45) / 5) * (a > 45 ? 1 : 0);
  const fade = tween(f, s(29.4), s(30), 1, 0);
  if (f < s(26)) return null;
  return (
    <AbsoluteFill style={{opacity: fade}}>
      <div style={{position: 'absolute', left: 900, top: 200, opacity: bg}}>
        <div style={{transform: `scale(${sp(8)})`, transformOrigin: 'left center', display: 'flex', alignItems: 'center', gap: 30}}>
          <Logo size={150} t={1} dark />
          <div style={{fontFamily: SERIF, color: C.cream, fontSize: 70, fontWeight: 700, lineHeight: 1.05}}>Pandey<br />Dental Clinics</div>
        </div>
        <div style={{fontFamily: SANS, color: C.cream, fontSize: 36, marginTop: 36, lineHeight: 1.7, opacity: sp(14)}}>
          Can't tell at home? Don't wait.<br />
          <b style={{color: C.teal}}>Visit your dentist.</b>
        </div>
        <div style={{marginTop: 34, display: 'inline-block', transform: `scale(${sp(20) * pulse})`, transformOrigin: 'left'}}>
          <div style={{background: C.teal, color: '#fff', fontFamily: SANS, fontWeight: 800, fontSize: 42, padding: '22px 50px', borderRadius: 60}}>Book a check-up</div>
        </div>
        <div style={{fontFamily: SANS, color: C.cream, opacity: sp(26) * 0.85, fontSize: 28, marginTop: 36}}>
          📍 [City] &nbsp; 📞 [Phone] &nbsp; @[handle]
        </div>
        <div style={{marginTop: 26, opacity: sp(32), display: 'flex', alignItems: 'center', gap: 16}}>
          <div style={{background: C.red, color: '#fff', fontFamily: SANS, fontWeight: 800, fontSize: 28, padding: '12px 28px', borderRadius: 12}}>▶ SUBSCRIBE</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const EndBg = () => {
  const f = useCurrentFrame();
  if (f < s(26)) return null;
  return <AbsoluteFill style={{background: `linear-gradient(135deg, ${C.maroon}, ${C.maroonDark})`, opacity: tween(f, s(26), s(26.6))}} />;
};

const Progress = () => {
  const f = useCurrentFrame();
  const w = interpolate(f, [0, s(26)], [0, 100], {extrapolateRight: 'clamp'});
  return <div style={{position: 'absolute', left: 0, bottom: 0, height: 10, width: `${w}%`, background: C.maroon, borderRight: `6px solid ${C.teal}`, opacity: f < s(3) || f > s(26) ? 0 : 1}} />;
};

export const Trailer = () => {
  const f = useCurrentFrame();
  const shrink = tween(f, s(26), s(26.8));
  const wipeAt = [s(20), s(23)].map((t) => tween(f, t - 6, t + 8, 0, 1) * tween(f, t + 8, t + 20, 1, 0) / 1);
  return (
    <AbsoluteFill style={{background: C.maroonDark}}>
      <EndBg />
      {CUTS.map((c, i) => (
        <Sequence key={i} from={s(c.at)} durationInFrames={s(c.len)}>
          <Footage src={c.src} shrink={i === 3 ? shrink : 0} />
        </Sequence>
      ))}
      <Sequence from={0} durationInFrames={s(3)}><Sting /></Sequence>
      <LowerThird />
      <TitleCard />
      <Causes />
      <Heal />
      <Progress />
      <EndCard />
      {/* soft maroon flash on cuts */}
      <AbsoluteFill style={{background: C.maroon, opacity: Math.max(...wipeAt) * 0.55, pointerEvents: 'none'}} />
    </AbsoluteFill>
  );
};
