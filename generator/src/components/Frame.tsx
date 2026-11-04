import React from "react";
import { BRAND, COLOR, FONT, SAFE } from "../theme";
import { Blueprint } from "./Blueprint";

type Props = {
  number: number;
  /** 0-based slide index */
  index: number;
  children: React.ReactNode;
};

const pad3 = (n: number) => String(n).padStart(3, "0");

/**
 * Shared chrome for every slide: series tag + page counter on top, handle + swipe
 * cue at the bottom. Consistent chrome is what makes 60 posts read as one series.
 */
export const Frame: React.FC<Props> = ({ number, index, children }) => {
  const last = index === BRAND.slides - 1;
  return (
    <Blueprint>
      <div
        style={{
          position: "absolute",
          left: SAFE.left,
          right: 1080 - SAFE.right,
          top: SAFE.top,
          display: "flex",
          justifyContent: "space-between",
          fontFamily: FONT.mono,
          fontSize: 28,
          letterSpacing: "0.2em",
        }}
      >
        <span style={{ color: COLOR.accent }}>
          {index === 0 ? BRAND.series : `${BRAND.series} · ${pad3(number)}`}
        </span>
        <span style={{ color: COLOR.textDim }}>
          {index + 1}/{BRAND.slides}
        </span>
      </div>
      {children}
      <div
        style={{
          position: "absolute",
          left: SAFE.left,
          right: 1080 - SAFE.right,
          bottom: 1350 - SAFE.bottom,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontFamily: FONT.mono,
          fontSize: 28,
        }}
      >
        <span style={{ color: COLOR.textDim, letterSpacing: "0.06em" }}>{BRAND.handle}</span>
        <span
          style={{
            color: COLOR.bgDeep,
            background: COLOR.accent,
            padding: "8px 18px",
            borderRadius: 10,
            fontWeight: 700,
            letterSpacing: "0.14em",
          }}
        >
          {last ? "SAVE · SHARE" : "SWIPE →"}
        </span>
      </div>
    </Blueprint>
  );
};

/** Coloured mono label above a headline: KAHANI / THE TRAP / THE FIX / SAVE THIS / YOUR TAKE? */
export const Kicker: React.FC<{ text: string; color: string; top?: number }> = ({ text, color, top = 150 }) => (
  <div
    style={{
      position: "absolute",
      left: SAFE.left,
      top,
      fontFamily: FONT.mono,
      fontWeight: 700,
      fontSize: 30,
      letterSpacing: "0.18em",
      color,
      border: `3px solid ${color}`,
      borderRadius: 10,
      padding: "6px 16px",
      boxShadow: `0 0 24px ${color}44`,
    }}
  >
    {text}
  </div>
);

/** Paragraph with *highlight* support, no animation. */
export const RichText: React.FC<{ text: string; size?: number; color?: string }> = ({
  text,
  size = 40,
  color = COLOR.text,
}) => (
  <div style={{ fontFamily: FONT.display, fontWeight: 500, fontSize: size, lineHeight: 1.36, color }}>
    {text.split(/(\*[^*]+\*|`[^`]+`)/).map((part, i) => {
      if (part.startsWith("*") && part.endsWith("*")) {
        return (
          <span key={i} style={{ color: COLOR.accent, fontWeight: 700 }}>
            {part.slice(1, -1)}
          </span>
        );
      }
      if (part.startsWith("`") && part.endsWith("`")) {
        return (
          <span key={i} style={{ fontFamily: FONT.mono, color: COLOR.accent, fontSize: size * 0.9 }}>
            {part.slice(1, -1)}
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    })}
  </div>
);
