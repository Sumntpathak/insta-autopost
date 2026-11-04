import React from "react";
import { Diagram } from "../components/Diagram";
import { Frame, Kicker, RichText } from "../components/Frame";
import { Headline } from "../components/Headline";
import type { Post } from "../lib/types";
import { COLOR, FONT, SAFE } from "../theme";

type SlideProps = { post: Post };

const W = SAFE.right - SAFE.left;
const at = (top: number, children: React.ReactNode, height?: number) => (
  <div style={{ position: "absolute", left: SAFE.left, width: W, top, height }}>{children}</div>
);

/** 1: giant number + hook headline + the trap diagram as the visual hook. */
export const CoverSlide: React.FC<SlideProps> = ({ post }) => (
  <Frame number={post.number} index={0}>
    {at(
      110,
      <div style={{ fontFamily: FONT.display, fontWeight: 700, fontSize: 200, lineHeight: 1, letterSpacing: "-0.04em", color: COLOR.text }}>
        {String(post.number).padStart(3, "0")}
      </div>,
    )}
    {at(340, <Headline text={post.cover.headline} words={[]} size={84} settled />)}
    <Diagram spec={post.trap.diagram} words={[]} settled area={{ left: 60, top: 760, width: 960, height: 380 }} />
  </Frame>
);

/** 2: the desi story + "kahani mein -> tech mein" mapping. */
export const StorySlide: React.FC<SlideProps> = ({ post }) => (
  <Frame number={post.number} index={1}>
    <Kicker text="KAHANI" color={COLOR.accent} />
    {at(230, <Headline text={post.story.headline} words={[]} size={76} settled />)}
    {at(470, <RichText text={post.story.body} />)}
    {at(
      790,
      <div
        style={{
          border: `3px solid ${COLOR.accent}88`,
          borderRadius: 24,
          background: `${COLOR.bgDeep}E6`,
          padding: "26px 34px",
          boxShadow: `0 0 50px ${COLOR.accent}22`,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: FONT.mono, fontSize: 24, letterSpacing: "0.18em", color: COLOR.textDim }}>
          <span>KAHANI MEIN</span>
          <span>TECH MEIN</span>
        </div>
        {post.story.mapping.map((row) => (
          <div key={row.story} style={{ display: "flex", alignItems: "center", gap: 20, marginTop: 22 }}>
            <span style={{ flex: 1, fontFamily: FONT.display, fontWeight: 700, fontSize: 44, color: COLOR.text }}>{row.story}</span>
            <span style={{ fontFamily: FONT.mono, fontSize: 40, color: COLOR.accent }}>→</span>
            <span
              style={{
                fontFamily: FONT.mono,
                fontWeight: 700,
                fontSize: 30,
                letterSpacing: "0.06em",
                color: COLOR.accent,
                border: `3px solid ${COLOR.accent}`,
                borderRadius: 12,
                padding: "8px 14px",
                whiteSpace: "nowrap",
              }}
            >
              {row.tech.toUpperCase()}
            </span>
          </div>
        ))}
      </div>,
    )}
  </Frame>
);

/** 3 + 4: the trap (red) and the fix (green), each a headline, diagram and one-line takeaway. */
const DiagramSlide: React.FC<SlideProps & { kind: "trap" | "fix" }> = ({ post, kind }) => {
  const part = post[kind];
  const color = kind === "trap" ? COLOR.failed : COLOR.confirmed;
  return (
    <Frame number={post.number} index={kind === "trap" ? 2 : 3}>
      <Kicker text={kind === "trap" ? "✕ THE TRAP" : "✓ THE FIX"} color={color} />
      {at(230, <Headline text={part.headline} words={[]} size={74} settled />)}
      <Diagram spec={part.diagram} words={[]} settled area={{ left: 60, top: 560, width: 960, height: 400 }} />
      {at(
        1040,
        <div style={{ borderLeft: `6px solid ${color}`, paddingLeft: 26 }}>
          <RichText text={part.body} size={38} />
        </div>,
      )}
    </Frame>
  );
};

export const TrapSlide: React.FC<SlideProps> = ({ post }) => <DiagramSlide post={post} kind="trap" />;
export const FixSlide: React.FC<SlideProps> = ({ post }) => <DiagramSlide post={post} kind="fix" />;

const Tick: React.FC = () => (
  <svg width={58} height={58} viewBox="0 0 64 64">
    <rect x={3} y={3} width={58} height={58} rx={14} fill="none" stroke={COLOR.confirmed} strokeWidth={4} />
    <path d="M17 33 L28 44 L48 22" fill="none" stroke={COLOR.confirmed} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

/** 5: the save trigger, a 4-line interview cheat sheet. */
export const SaveSlide: React.FC<SlideProps> = ({ post }) => (
  <Frame number={post.number} index={4}>
    <Kicker text="SAVE THIS" color={COLOR.accent} />
    {at(230, <Headline text={`Interview cheat sheet: *${post.topic}*`} words={[]} size={74} settled />)}
    {at(
      540,
      <div
        style={{
          border: `3px solid ${COLOR.accent}`,
          borderRadius: 28,
          background: `${COLOR.bgDeep}E6`,
          padding: "34px 40px",
          boxShadow: `0 0 60px ${COLOR.accent}33`,
        }}
      >
        <div style={{ fontFamily: FONT.mono, fontSize: 26, letterSpacing: "0.16em", color: COLOR.accent, marginBottom: 10 }}>
          {`// ${post.topic.toUpperCase()}`}
        </div>
        {post.save.items.map((item) => (
          <div key={item} style={{ display: "flex", alignItems: "center", gap: 26, margin: "22px 0" }}>
            <Tick />
            <span style={{ fontFamily: FONT.display, fontWeight: 700, fontSize: 50, color: COLOR.text }}>{item}</span>
          </div>
        ))}
      </div>,
    )}
    {at(1110, <RichText text="*Save karo.* Interview se pehle 30 second mein revise." size={36} color={COLOR.textDim} />)}
  </Frame>
);

/** 6: the comment + share + follow trigger. */
export const CtaSlide: React.FC<SlideProps> = ({ post }) => (
  <Frame number={post.number} index={5}>
    <Kicker text="YOUR TAKE?" color={COLOR.accent} />
    {at(230, <Headline text={post.cta.question} words={[]} size={76} settled />)}
    {at(
      530,
      <div>
        {post.cta.options.map((opt, i) => (
          <div
            key={opt}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 26,
              marginBottom: 24,
              padding: "26px 30px",
              border: `3px solid ${COLOR.accent}`,
              borderRadius: 18,
              background: `${COLOR.bgDeep}E6`,
              boxShadow: `0 0 26px ${COLOR.accent}33`,
            }}
          >
            <span style={{ fontFamily: FONT.mono, fontWeight: 700, fontSize: 44, color: COLOR.accent }}>{i === 0 ? "A" : "B"}</span>
            <span style={{ fontFamily: FONT.display, fontWeight: 700, fontSize: 48, color: COLOR.text }}>{opt}</span>
          </div>
        ))}
        <div style={{ fontFamily: FONT.mono, fontSize: 32, color: COLOR.accent, marginTop: 6 }}>Comment A ya B ↓</div>
      </div>,
    )}
    {at(
      950,
      <div style={{ borderTop: `2px solid ${COLOR.grid}`, paddingTop: 34 }}>
        <RichText text={`Follow *${"@shipstack_"}* for 2 system design breakdowns daily.`} size={40} />
        <div style={{ marginTop: 16 }}>
          <RichText text="Share with the dost who has an interview this week." size={34} color={COLOR.textDim} />
        </div>
      </div>,
    )}
  </Frame>
);

export const SLIDES = [CoverSlide, StorySlide, TrapSlide, FixSlide, SaveSlide, CtaSlide] as const;
