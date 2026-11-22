import {AbsoluteFill, Freeze, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {C, DOCTOR, NAME, SANS, SERIF} from './brand';
import {Logo} from './Logo';
import {Banner, Icon, Panel, glass, sec, tw, useSp, useWin} from './ui';

export const SRC_FRAMES = 6275;          // footage length (209.2 s)
export const END_CARD_FRAMES = sec(8);   // extra seconds for the YouTube end screen
export const TOTAL = SRC_FRAMES + END_CARD_FRAMES;

// Full-frame cutaways inside the footage: overlays hide during these.
const CUTAWAYS: [number, number][] = [[54.6, 57.3], [67.5, 70.2], [88, 92.7], [127.7, 130.8], [173.8, 176]];
const CHAPTERS = [
  {at: 0, n: 'INTRO', c: C.gold, end: 23.6},
  {at: 23.6, n: 'NORMAL ULCER', c: C.teal, end: 151.7},
  {at: 151.7, n: 'CANCEROUS ULCER', c: C.red, end: 199},
  {at: 199, n: 'WHAT TO DO', c: C.gold, end: 209.2},
];
const END_AT = 205.5;

const useHide = () => {
  const t = useCurrentFrame() / 30;
  let h = 0;
  for (const [a, b] of CUTAWAYS) {
    const v = Math.min(1, Math.max(0, (t - (a - 0.2)) / 0.2)) * Math.min(1, Math.max(0, (b + 0.2 - t) / 0.2));
    h = Math.max(h, v);
  }
  return 1 - h;
};

const Footage = () => {
  const f = useCurrentFrame();
  const shrink = tw(f, sec(END_AT), sec(END_AT + 1));
  const push = 1.015 + 0.025 * (0.5 + 0.5 * Math.sin(f / (30 * 7)));
  const W = 1920 - shrink * (1920 - 800), H = 1080 - shrink * (1080 - 450);
  return (
    <div style={{position: 'absolute', left: shrink * 90, top: shrink * 300, width: W, height: H, overflow: 'hidden', borderRadius: shrink * 30,
      border: shrink ? `3px solid ${C.gold}` : undefined, boxShadow: shrink ? '0 24px 70px rgba(0,0,0,.5)' : undefined}}>
      <div style={{width: '100%', height: '100%', transform: `scale(${push})`}}>
        <Sequence from={0} durationInFrames={SRC_FRAMES}><OffthreadVideo src={staticFile('footage.mp4')} style={{width: '100%', height: '100%', objectFit: 'cover'}} /></Sequence>
        <Sequence from={SRC_FRAMES}>
          <Freeze frame={0}><OffthreadVideo muted startFrom={SRC_FRAMES - 3} src={staticFile('footage.mp4')} style={{width: '100%', height: '100%', objectFit: 'cover'}} /></Freeze>
        </Sequence>
      </div>
    </div>
  );
};

const Vignette = () => {
  const f = useCurrentFrame();
  const o = 1 - tw(f, sec(END_AT), sec(END_AT + 1));
  return <AbsoluteFill style={{opacity: o, background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(30,4,14,.55) 100%)'}} />;
};

const Sting = () => {
  const f = useCurrentFrame();
  const wipe = tw(f, sec(2), sec(2.8), 0, 105);
  const logoT = tw(f, 3, sec(1.3));
  const text = tw(f, sec(1.1), sec(1.7));
  if (f > sec(3)) return null;
  return (
    <AbsoluteFill style={{background: `radial-gradient(circle at 50% 40%, #8c1b3d, ${C.maroonDeep} 70%)`, transform: `translateX(${wipe}%)`, alignItems: 'center', justifyContent: 'center'}}>
      <div style={{textAlign: 'center', transform: `translateX(${-wipe * 0.3}%)`}}>
        <Logo size={250} t={logoT} light />
        <div style={{fontFamily: SERIF, fontWeight: 800, color: C.cream, fontSize: 92, marginTop: 22, opacity: text, transform: `translateY(${(1 - text) * 26}px)`}}>{NAME}</div>
        <div style={{fontFamily: SANS, fontWeight: 600, color: C.gold, fontSize: 28, letterSpacing: 9, marginTop: 8, opacity: text}}>COMPASSIONATE DENTAL CARE</div>
      </div>
    </AbsoluteFill>
  );
};

const LowerThird = () => {
  const o = useWin(3.4, 9.5);
  const sp = useSp();
  if (o < 0.01) return null;
  const line = tw(useCurrentFrame(), sec(3.4), sec(4.2));
  return (
    <div style={{position: 'absolute', left: 70, bottom: 80, opacity: o, transform: `translateX(${(1 - sp(3.4)) * -140}px)`}}>
      <div style={{...glass(C.gold), padding: '20px 40px 20px 30px', display: 'flex', alignItems: 'center', gap: 22}}>
        <Logo size={64} light />
        <div>
          <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 52, color: C.cream, lineHeight: 1.1}}>{DOCTOR}</div>
          <div style={{fontFamily: SANS, fontWeight: 500, fontSize: 24, letterSpacing: 3, color: C.gold, marginTop: 4}}>{NAME.toUpperCase()}</div>
        </div>
      </div>
      <div style={{height: 4, width: `${line * 100}%`, background: C.gold, marginTop: 8, borderRadius: 2}} />
    </div>
  );
};

const Hero = () => {
  const o = useWin(8, 14.6);
  const sp = useSp();
  if (o < 0.01) return null;
  return (
    <>
      <div style={{position: 'absolute', top: 50, left: 0, right: 0, display: 'flex', justifyContent: 'center', opacity: o, transform: `translateY(${(1 - sp(8)) * -60}px)`}}>
        <div style={{...glass(C.gold), padding: '22px 60px', textAlign: 'center'}}>
          <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 22, letterSpacing: 7, color: C.gold}}>TODAY'S TOPIC</div>
          <div style={{fontFamily: SERIF, fontWeight: 800, fontSize: 74, color: C.cream, lineHeight: 1.1}}>Normal vs Cancerous Mouth Ulcer</div>
        </div>
      </div>
      <div style={{position: 'absolute', left: 44, top: 470, opacity: o, transform: `translateX(${(1 - sp(10)) * -400}px)`}}>
        <Chip color={C.teal} icon="check" label="NORMAL" sub="No cause for worry" />
      </div>
      <div style={{position: 'absolute', right: 44, top: 470, opacity: o, transform: `translateX(${(1 - sp(10.6)) * 400}px)`}}>
        <Chip color={C.red} icon="alert" label="NEEDS A CHECK" sub="Visit your dentist urgently" />
      </div>
    </>
  );
};
const Chip = ({color, icon, label, sub}: {color: string; icon: string; label: string; sub: string}) => (
  <div style={{...glass(color), padding: '18px 28px', width: 440}}>
    <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
      <Icon name={icon} size={38} color={color} />
      <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 38, color: '#fff', letterSpacing: 1}}>{label}</div>
    </div>
    <div style={{fontFamily: SANS, fontWeight: 500, fontSize: 24, color: '#ffffffcc', marginTop: 4}}>{sub}</div>
  </div>
);

const ChapterPill = () => {
  const t = useCurrentFrame() / 30;
  const idx = CHAPTERS.findIndex((c) => t >= c.at && t < c.end);
  const ch = CHAPTERS[Math.max(0, idx)];
  const o = Math.min(tw(t, 14.6, 15.2), tw(t, END_AT - 0.6, END_AT, 1, 0));
  const pop = tw(t, ch.at + 0.05, ch.at + 0.6);
  if (o < 0.01) return null;
  return (
    <div style={{position: 'absolute', left: 44, top: 44, opacity: o * Math.min(1, 0.4 + pop)}}>
      <div style={{...glass(ch.c), borderTopWidth: 0, borderLeft: `8px solid ${ch.c}`, padding: '10px 26px', borderRadius: 16, display: 'flex', gap: 14, alignItems: 'center'}}>
        <span style={{fontFamily: SANS, fontWeight: 700, fontSize: 24, color: ch.c}}>{idx > 0 ? String(idx).padStart(2, '0') : '00'}</span>
        <span style={{fontFamily: SANS, fontWeight: 700, fontSize: 24, letterSpacing: 4, color: '#fff'}}>{ch.n}</span>
      </div>
    </div>
  );
};

/** Big chapter title. It sits exactly over the clip's original plain caption to cover it. */
const ChapterCard = ({start, end, n, title, sub, color}: {start: number; end: number; n: string; title: string; sub: string; color: string}) => {
  const o = useWin(start, end);
  const sp = useSp();
  if (o < 0.01) return null;
  return (
    <div style={{position: 'absolute', left: 190, width: 1540, top: 845, height: 175, opacity: o, transform: `scale(${0.94 + 0.06 * sp(start)})`,
      ...glass(color), background: `linear-gradient(100deg, ${color}, ${C.maroonDeep} 70%)`, backdropFilter: 'none', border: `2px solid ${C.gold}`, borderTop: `2px solid ${C.gold}`,
      display: 'flex', alignItems: 'center', gap: 36, padding: '0 50px'}}>
      <div style={{fontFamily: SERIF, fontWeight: 800, fontSize: 110, color: C.gold, lineHeight: 1}}>{n}</div>
      <div style={{width: 3, height: 100, background: C.gold, opacity: 0.6}} />
      <div>
        <div style={{fontFamily: SERIF, fontWeight: 800, fontSize: 84, color: '#fff', lineHeight: 1.05}}>{title}</div>
        <div style={{fontFamily: SANS, fontWeight: 500, fontSize: 30, color: C.cream, letterSpacing: 2, marginTop: 4}}>{sub}</div>
      </div>
    </div>
  );
};

const HealCard = () => {
  const o = useWin(131, 135.6);
  const sp = useSp();
  const f = useCurrentFrame();
  if (o < 0.01) return null;
  const day = Math.min(4, 1 + Math.floor(tw(f, sec(131.6), sec(134)) * 3.999));
  return (
    <div style={{position: 'absolute', right: 44, top: 150, width: 470, opacity: o, transform: `scale(${0.8 + 0.2 * sp(131)})`, transformOrigin: 'top right', ...glass(C.teal), padding: '24px 28px', textAlign: 'center'}}>
      <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 20, letterSpacing: 4, color: C.teal}}>NORMAL ULCER</div>
      <div style={{fontFamily: SERIF, fontWeight: 800, fontSize: 118, color: C.cream, lineHeight: 1.05}}>3–4</div>
      <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 44, color: C.cream}}>days to heal on its own</div>
      <div style={{display: 'flex', gap: 10, marginTop: 16}}>
        {[1, 2, 3, 4].map((d) => <div key={d} style={{flex: 1, height: 12, borderRadius: 6, background: d <= day ? C.teal : 'rgba(255,255,255,.2)'}} />)}
      </div>
    </div>
  );
};

const ProgressBar = () => {
  const t = useCurrentFrame() / 30;
  const o = Math.min(tw(t, 3, 3.6), tw(t, END_AT - 0.6, END_AT, 1, 0));
  const total = 209.2;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 10, display: 'flex', gap: 4, opacity: o}}>
      {CHAPTERS.map((c) => {
        const w = ((c.end - c.at) / total) * 100;
        const fill = Math.min(1, Math.max(0, (t - c.at) / (c.end - c.at)));
        return <div key={c.n} style={{width: `${w}%`, background: 'rgba(0,0,0,.45)'}}><div style={{width: `${fill * 100}%`, height: '100%', background: c.c}} /></div>;
      })}
    </div>
  );
};

const EndCard = () => {
  const f = useCurrentFrame();
  const sp = useSp();
  const bg = tw(f, sec(END_AT), sec(END_AT + 1.2));
  if (f < sec(END_AT)) return null;
  const pulse = 1 + 0.04 * Math.sin(Math.max(0, f - sec(END_AT + 3)) / 6);
  const fade = tw(f, TOTAL - 20, TOTAL, 1, 0);
  const x = 960;
  return (
    <AbsoluteFill style={{opacity: fade}}>
      <AbsoluteFill style={{background: `radial-gradient(circle at 70% 30%, #8c1b3d, ${C.maroonDeep} 75%)`, opacity: bg, zIndex: -1}} />
      <div style={{position: 'absolute', left: x, top: 90, opacity: bg}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 26, transform: `translateY(${(1 - sp(END_AT + 0.6)) * 30}px)`}}>
          <Logo size={110} light />
          <div style={{fontFamily: SERIF, fontWeight: 800, color: C.cream, fontSize: 64, lineHeight: 1.05}}>Pandey<br />Dental Clinics</div>
        </div>
        <div style={{marginTop: 40, opacity: sp(END_AT + 1.2), transform: `translateY(${(1 - sp(END_AT + 1.2)) * 30}px)`}}>
          <div style={{display: 'flex', gap: 14, alignItems: 'center'}}><Icon name="ban" size={40} color={C.gold} />
            <span style={{fontFamily: SERIF, fontWeight: 700, fontSize: 50, color: C.cream}}>Don't try home remedies.</span></div>
          <div style={{fontFamily: SERIF, fontWeight: 800, fontSize: 60, color: C.gold, marginTop: 6}}>See your dentist immediately.</div>
        </div>
        <div style={{marginTop: 38, display: 'flex', gap: 24, alignItems: 'center', opacity: sp(END_AT + 2)}}>
          <div style={{transform: `scale(${pulse})`, background: `linear-gradient(135deg, ${C.teal}, #1b8f82)`, color: '#fff', fontFamily: SANS, fontWeight: 700, fontSize: 36, padding: '20px 46px', borderRadius: 60, boxShadow: '0 12px 30px rgba(0,0,0,.4)'}}>Book a check-up</div>
          <div style={{background: C.red, color: '#fff', fontFamily: SANS, fontWeight: 700, fontSize: 28, padding: '16px 32px', borderRadius: 14}}>SUBSCRIBE</div>
        </div>
        <div style={{marginTop: 30, fontFamily: SANS, fontWeight: 500, fontSize: 28, color: C.cream, opacity: sp(END_AT + 2.6) * 0.9}}>[City]  ·  [Phone]  ·  @[handle]</div>
      </div>
      {/* reserved boxes for YouTube end-screen elements */}
      <div style={{position: 'absolute', right: 90, bottom: 70, width: 640, height: 190, borderRadius: 18, border: '2px dashed rgba(255,255,255,.35)', opacity: 0}} />
    </AbsoluteFill>
  );
};

export const Video = () => {
  const hide = useHide();
  return (
    <AbsoluteFill style={{background: C.maroonDeep}}>
      <Footage />
      <Vignette />
      <div style={{opacity: hide}}>
        <LowerThird />
        <Hero />
        {/* Normal ulcer */}
        <Panel side="left" start={57.4} end={80} eyebrow="NORMAL ULCER" title="Burning pain with" accent={C.teal} items={[
          {icon: 'drop', text: 'Sour food', at: 60}, {icon: 'flame', text: 'Spicy food', at: 62.5}, {icon: 'candy', text: 'Even sweet food', at: 65}, {icon: 'thermo', text: 'Hot water', at: 70.6}]} />
        <Panel side="right" start={84} end={100} eyebrow="HOW IT LOOKS" title="A normal ulcer has" accent={C.teal} items={[
          {icon: 'ring', text: 'A red border', at: 84.4}, {icon: 'candy', text: 'White or yellow centre', at: 92.8}, {icon: 'soft', text: 'Surrounding area never feels hard', at: 95.8}]} />
        <Panel side="left" start={107} end={124} eyebrow="OFTEN SEEN WITH" title="Common triggers" accent={C.teal} items={[
          {icon: 'thermo', text: 'Fever', at: 110.2}, {icon: 'drop', text: 'Low water intake', at: 112.5}, {icon: 'bowl', text: 'Poor diet', at: 115.3}, {icon: 'flame', text: 'Very spicy food', at: 118.4}]} />
        <HealCard />
        <Panel side="right" start={135.8} end={151.5} eyebrow="CARE" title="No heavy treatment needed" accent={C.teal} items={[
          {icon: 'home', text: 'Simple home tips', at: 139.2}, {icon: 'pill', text: 'A soothing gel', at: 146.2}]} />
        {/* Cancerous ulcer */}
        <Panel side="right" start={160} end={178} eyebrow="RISK FACTORS" title="What can cause it" accent={C.red} top={130} items={[
          {icon: 'virus', text: 'HPV virus', at: 162.9}, {icon: 'rub', text: 'Constant rubbing or injury', at: 165}, {icon: 'saw', text: 'Sharp tooth edges', at: 168.4},
          {icon: 'smoke', text: 'Gutka, tobacco, bidi, cigarette', at: 172.2}, {icon: 'glass', text: 'Alcohol', at: 175.9}]} />
        <Banner start={179} end={191.5} icon="alert" accent={C.red} big="No bad habits? It can still happen." small="Never assume a mouth ulcer is harmless" />
        <Banner start={192} end={204.4} icon="home" accent={C.gold} big="You can't tell them apart at home" small="Don't wait. Get it checked." />
      </div>
      <ChapterCard start={31.1} end={36.5} n="01" title="Normal Ulcer" sub="WHAT IT LOOKS LIKE · WHEN IT HEALS" color={C.teal} />
      <ChapterCard start={152} end={157.6} n="02" title="Cancerous Ulcer" sub="RISK FACTORS · WHAT TO WATCH FOR" color={C.red} />
      <ChapterPill />
      <ProgressBar />
      <Sting />
      <EndCard />
    </AbsoluteFill>
  );
};
