import React from "react";
import type { IconName } from "../lib/types";

/** Line-art icons on a 64x64 grid, drawn with the current stroke colour. */
const PATHS: Record<IconName, React.ReactNode> = {
  phone: (
    <>
      <rect x={18} y={4} width={28} height={56} rx={6} />
      <line x1={28} y1={52} x2={36} y2={52} />
      <rect x={22} y={10} width={20} height={36} rx={2} opacity={0.5} />
    </>
  ),
  server: (
    <>
      <rect x={8} y={6} width={48} height={14} rx={3} />
      <rect x={8} y={25} width={48} height={14} rx={3} />
      <rect x={8} y={44} width={48} height={14} rx={3} />
      <circle cx={16} cy={13} r={1.5} />
      <circle cx={16} cy={32} r={1.5} />
      <circle cx={16} cy={51} r={1.5} />
    </>
  ),
  db: (
    <>
      <ellipse cx={32} cy={12} rx={22} ry={7} />
      <path d="M10 12 V50 Q32 64 54 50 V12" />
      <path d="M10 31 Q32 45 54 31" />
    </>
  ),
  user: (
    <>
      <circle cx={32} cy={20} r={11} />
      <path d="M12 58 Q14 36 32 36 Q50 36 52 58" />
    </>
  ),
  chip: (
    <>
      <rect x={16} y={16} width={32} height={32} rx={4} />
      <rect x={24} y={24} width={16} height={16} opacity={0.6} />
      {[22, 32, 42].map((p) => (
        <g key={p}>
          <line x1={p} y1={6} x2={p} y2={16} />
          <line x1={p} y1={48} x2={p} y2={58} />
          <line x1={6} y1={p} x2={16} y2={p} />
          <line x1={48} y1={p} x2={58} y2={p} />
        </g>
      ))}
    </>
  ),
  cache: (
    <>
      <rect x={8} y={10} width={48} height={44} rx={6} />
      <path d="M36 16 L24 34 H34 L28 48 L42 28 H32 Z" />
    </>
  ),
  lock: (
    <>
      <rect x={12} y={28} width={40} height={30} rx={5} />
      <path d="M20 28 V20 Q20 8 32 8 Q44 8 44 20 V28" />
      <line x1={32} y1={38} x2={32} y2={47} />
    </>
  ),
  clock: (
    <>
      <circle cx={32} cy={32} r={24} />
      <path d="M32 18 V32 L42 38" />
    </>
  ),
  seat: (
    <>
      <path d="M18 8 H40 Q44 8 44 12 V34 H18 Z" />
      <path d="M12 34 H50 V42 H12 Z" />
      <line x1={16} y1={42} x2={16} y2={58} />
      <line x1={46} y1={42} x2={46} y2={58} />
    </>
  ),
  queue: (
    <>
      {[8, 22, 36, 50].map((x) => (
        <g key={x}>
          <circle cx={x + 3} cy={22} r={5} />
          <path d={`M${x - 3} 44 Q${x + 3} 30 ${x + 9} 44`} />
        </g>
      ))}
    </>
  ),
};

export const Icon: React.FC<{ name: IconName; size: number; color: string }> = ({ name, size, color }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 64 64"
    fill="none"
    stroke={color}
    strokeWidth={3}
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{ filter: `drop-shadow(0 0 6px ${color})`, overflow: "visible" }}
  >
    {PATHS[name]}
  </svg>
);
