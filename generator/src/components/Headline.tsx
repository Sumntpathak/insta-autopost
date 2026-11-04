import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { wordFrame } from "../lib/sync";
import type { Word } from "../lib/types";
import { COLOR, FONT } from "../theme";

type Token = { text: string; kind: "plain" | "hl" | "code" };

/** "Cache added. Why is the DB *still down*?" -> plain / highlight / `code` tokens (word level). */
export const parseMarkup = (text: string): Token[] =>
  text.split(/(\*[^*]+\*|`[^`]+`)/).flatMap<Token>((part) => {
    if (part.startsWith("*") && part.endsWith("*")) {
      return part.slice(1, -1).split(/\s+/).filter(Boolean).map((t) => ({ text: t, kind: "hl" }));
    }
    if (part.startsWith("`") && part.endsWith("`")) return [{ text: part.slice(1, -1), kind: "code" }];
    return part.split(/\s+/).filter(Boolean).map((t) => ({ text: t, kind: "plain" }));
  });

type Props = {
  text: string;
  words: Word[];
  /** "type" = typewriter with caret (hooks), "pop" = words spring in */
  mode?: "type" | "pop";
  startFrame?: number;
  size?: number;
  /** render fully settled (covers / stills) */
  settled?: boolean;
};

const CHARS_PER_FRAME = 1.6;

/**
 * Left-aligned bold headline. Highlighted words turn yellow and get a glowing
 * underline that draws exactly when the voiceover says them.
 */
export const Headline: React.FC<Props> = ({ text, words, mode = "pop", startFrame = 0, size = 96, settled = false }) => {
  const current = useCurrentFrame();
  const frame = settled ? 10_000 : current;
  const { fps } = useVideoConfig();
  const tokens = parseMarkup(text);
  const totalChars = tokens.reduce((n, t) => n + t.text.length + 1, 0);
  const typed = mode === "type" ? Math.floor((frame - startFrame) * CHARS_PER_FRAME) : totalChars;
  const caretOn = mode === "type" && Math.floor(frame / 15) % 2 === 0;
  let charCursor = 0;

  return (
    <div
      style={{
        fontFamily: FONT.display,
        fontWeight: 700,
        fontSize: size,
        lineHeight: 1.06,
        letterSpacing: "-0.025em",
        color: COLOR.text,
      }}
    >
      {tokens.map((tok, i) => {
        const tokStart = charCursor;
        charCursor += tok.text.length + 1;
        const visibleChars = Math.max(0, Math.min(tok.text.length, typed - tokStart));
        if (mode === "type" && visibleChars === 0) return null;
        const shown = mode === "type" ? tok.text.slice(0, visibleChars) : tok.text;
        const pop = mode === "pop" ? spring({ frame: frame - startFrame - i * 3, fps, config: { damping: 15, stiffness: 170 } }) : 1;
        const spokenAt = wordFrame(words, tok.text, fps, startFrame + 12 + i * 3);
        const underline = tok.kind === "hl"
          ? interpolate(frame - spokenAt, [0, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
          : 0;
        return (
          <span
            key={`${tok.text}-${i}`}
            style={{
              position: "relative",
              display: "inline-block",
              marginRight: size * 0.24,
              opacity: pop,
              transform: `translateY(${interpolate(pop, [0, 1], [size * 0.4, 0])}px)`,
              color: tok.kind === "hl" ? COLOR.accent : COLOR.text,
              ...(tok.kind === "code" && {
                fontFamily: FONT.mono,
                fontWeight: 500,
                fontSize: size * 0.74,
                color: COLOR.accent,
                border: `3px solid ${COLOR.accent}88`,
                borderRadius: 14,
                padding: `0 ${size * 0.16}px`,
                boxShadow: `0 0 28px ${COLOR.accent}33`,
              }),
            }}
          >
            {shown}
            {tok.kind === "hl" && (
              <span
                style={{
                  position: "absolute",
                  left: 0,
                  bottom: -size * 0.06,
                  height: size * 0.07,
                  width: `${underline * 100}%`,
                  background: COLOR.accent,
                  borderRadius: 4,
                  boxShadow: `0 0 16px ${COLOR.accent}`,
                }}
              />
            )}
          </span>
        );
      })}
      {mode === "type" && (
        <span
          style={{
            display: "inline-block",
            width: size * 0.07,
            height: size * 0.9,
            background: COLOR.accent,
            verticalAlign: "-0.1em",
            opacity: caretOn || settled ? 1 : 0,
          }}
        />
      )}
    </div>
  );
};
