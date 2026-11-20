// ShipStack logo sting (4 s): a terminal cursor stretches into a waterline, the hull rises out of it,
// the code-chevron sail draws itself and snaps up, the boat starts to bob on the water, and "shipstack_" types out.
// Use it as the intro or outro of any reel. Geometry matches reels/shipstack/studio/theme.py (draw_boat).
import {Audio} from '@remotion/media';
import React from 'react';
import {AbsoluteFill, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

const BG = '#0D1117';
const ACCENT = '#22D3EE';
const TEXT = '#E6EDF3';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const SAIL = 'M3.5 2 L4.9375 2 L6.9 3.75 L4.9375 5.5 L3.5 5.5 L5.4625 3.75 Z';

export type LogoStingProps = {square?: boolean};

export const LogoSting: React.FC<LogoStingProps> = ({square = false}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = (sec: number) => sec * fps;
  const size = square ? 420 : 480;
  const sailing = frame > s(1.7);
  const bob = sailing ? Math.sin((frame - s(1.7)) / fps * 3.2) * 0.07 : 0;          // in grid units
  const word = 'shipstack';
  const typed = Math.max(0, Math.min(word.length, Math.floor((frame - s(1.95)) / 2)));
  const cursorOn = Math.floor(frame / (fps / 2)) % 2 === 0;

  return (
    <AbsoluteFill style={{background: BG, justifyContent: 'center', alignItems: 'center'}}>
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center',
        scale: interpolate(frame, [s(2.6), s(4)], [1, 1.03], {...clamp, output: 'perceptual-scale'}),
        translate: `0px ${square ? -20 : -60}px`}}>
        <svg width={size} height={size} viewBox="0 0 10 10" style={{overflow: 'visible'}}>
          <g style={{translate: `0px ${bob}px`}}>
            {/* 1. cursor -> waterline: a blinking bar that stretches to the hull's width */}
            <rect x={interpolate(frame, [s(0.4), s(1.0)], [4.8, 1.9], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)})}
              width={interpolate(frame, [s(0.4), s(1.0)], [0.4, 6.2], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)})}
              y={6.0} height={0.3} fill={ACCENT}
              opacity={frame < s(0.4) ? (cursorOn ? 1 : 0.2) : interpolate(frame, [s(1.0), s(1.2)], [1, 0], clamp)} />
            {/* 2. the hull rises out of the waterline */}
            <polygon points="1.9,6.15 8.1,6.15 6.85,7.9 3.15,7.9" fill={ACCENT}
              style={{transformOrigin: '5px 6.15px', transformBox: 'view-box',
                scale: `1 ${interpolate(frame, [s(0.85), s(1.35)], [0, 1], {...clamp, easing: Easing.spring({damping: 14})})}`}} />
            {/* 3. the sail draws itself, fills, then snaps up into place */}
            <g style={{translate: `0px ${interpolate(frame, [s(1.45), s(1.75)], [0.9, 0], {...clamp, easing: Easing.spring({damping: 10})})}px`}}>
              <path d={SAIL} fill="none" stroke={ACCENT} strokeWidth={0.12} strokeLinejoin="round" opacity={frame < s(1.15) ? 0 : 1}
                pathLength={1} strokeDasharray={1}
                strokeDashoffset={interpolate(frame, [s(1.15), s(1.55)], [1, 0], {...clamp, easing: Easing.bezier(0.65, 0, 0.35, 1)})} />
              <path d={SAIL} fill={ACCENT} opacity={interpolate(frame, [s(1.5), s(1.65)], [0, 1], clamp)} />
            </g>
          </g>
        </svg>
        {/* 5. wordmark types out, the cyan cursor (the handle's underscore) keeps blinking */}
        <div style={{fontFamily: 'Geist, sans-serif', fontWeight: 800, fontSize: square ? 116 : 132, letterSpacing: -5,
          color: TEXT, height: square ? 140 : 160, display: 'flex', alignItems: 'flex-end', marginTop: square ? -10 : -20}}>
          <span>{word.slice(0, typed)}</span>
          <span style={{display: 'inline-block', width: square ? 62 : 72, height: square ? 14 : 16, marginLeft: 8, marginBottom: square ? 22 : 26,
            background: ACCENT, opacity: frame < s(1.95) ? 0 : typed < word.length || cursorOn ? 1 : 0.15}} />
        </div>
      </div>
      <Audio name="Logo sound" src={staticFile('sfx/logo-sting.wav')} />
    </AbsoluteFill>
  );
};
