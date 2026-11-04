import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { wordFrame } from "../lib/sync";
import type { Diagram as DiagramSpec, DiagramNode, NodeState, Word } from "../lib/types";
import { BODY, COLOR, FONT, type Area } from "../theme";
import { Icon } from "./Icons";

const BOX = { w: 260, h: 104 } as const;
const ICON_SIZE = 120;

const stateColor = (s: NodeState): string =>
  ({ idle: COLOR.accent, hot: COLOR.accent, fail: COLOR.failed, ok: COLOR.confirmed, dim: COLOR.textDim })[s];

const toPxIn = (area: Area) => (n: { x: number; y: number }): [number, number] => [
  area.left + (n.x / 100) * area.width,
  area.top + (n.y / 100) * area.height,
];

/** Wires run vertically only when the target is clearly above/below; otherwise they leave from the sides. */
const isVertical = (dx: number, dy: number): boolean => Math.abs(dy) >= 40 && Math.abs(dy) >= Math.abs(dx) * 0.5;

/** Boxes grow with their text (minWidth 260); estimate the real width so wires meet the border. */
const boxWidth = (n: DiagramNode): number => {
  const label = n.label.length * 19.1; // JetBrains Mono 28px + 0.08em tracking
  const sub = (n.sub?.length ?? 0) * 13.2;
  return Math.max(BOX.w, 52 + (n.icon ? 64 : 0) + Math.max(label, sub) + 6);
};

type Curve = [number, number, number, number, number, number, number, number];

/** Vertical-biased cubic between two points (wires go down/up like the reference diagrams). */
const curveBetween = (a: [number, number], b: [number, number]): Curve => {
  const dy = b[1] - a[1];
  const dx = b[0] - a[0];
  if (!isVertical(dx, dy)) return [a[0], a[1], a[0] + dx * 0.5, a[1], b[0] - dx * 0.5, b[1], b[0], b[1]];
  return [a[0], a[1], a[0], a[1] + dy * 0.55, b[0], b[1] - dy * 0.55, b[0], b[1]];
};

const pointAt = (c: Curve, t: number): [number, number] => {
  const u = 1 - t;
  const x = u * u * u * c[0] + 3 * u * u * t * c[2] + 3 * u * t * t * c[4] + t * t * t * c[6];
  const y = u * u * u * c[1] + 3 * u * u * t * c[3] + 3 * u * t * t * c[5] + t * t * t * c[7];
  return [x, y];
};

const pathD = (c: Curve): string => `M${c[0]} ${c[1]} C${c[2]} ${c[3]} ${c[4]} ${c[5]} ${c[6]} ${c[7]}`;

/** Edge endpoint on the node's border facing the other node. */
/** Icon nodes are a column: 120px glyph + label below, centred on (x, y). */
const ICON_COLUMN = { glyphCenterDy: -22, top: -90, bottom: 92, side: 78 } as const;

const anchorIn = (toPx: ReturnType<typeof toPxIn>) => (n: DiagramNode, toward: [number, number]): [number, number] => {
  const [x, y] = toPx(n);
  const dy = toward[1] - y;
  const dx = toward[0] - x;
  const vertical = isVertical(dx, dy);
  if (n.kind === "icon") {
    // leave from the glyph's side, or clear of the label when going down, so wires never cross the name
    if (!vertical) return [x + Math.sign(dx) * ICON_COLUMN.side, y + ICON_COLUMN.glyphCenterDy];
    return [x, y + (dy > 0 ? ICON_COLUMN.bottom : ICON_COLUMN.top)];
  }
  if (vertical) return [x, y + Math.sign(dy) * (BOX.h / 2)];
  return [x + Math.sign(dx) * (boxWidth(n) / 2), y];
};

type Props = { spec: DiagramSpec; words: Word[]; settled?: boolean; area?: Area };

/**
 * Glowing line-art system diagram, the series' signature visual. Nodes pop in when
 * their word is spoken, wires draw on, packets flow, states flip (hot -> fail -> ok)
 * on cue. Coordinates are percentages of the BODY box, so specs stay simple.
 */
export const Diagram: React.FC<Props> = ({ spec, words, settled = false, area = BODY }) => {
  const toPx = toPxIn(area);
  const anchor = anchorIn(toPx);
  const current = useCurrentFrame();
  const frame = settled ? 10_000 : current;
  const { fps } = useVideoConfig();
  const byId = new Map(spec.nodes.map((n) => [n.id, n]));
  const appearAt = (on: string | undefined, fallback: number) => (on ? wordFrame(words, on, fps, fallback) : fallback);
  const nodeAt = new Map(spec.nodes.map((n, i) => [n.id, appearAt(n.on, 6 + i * 8)]));
  const stateOf = (base: NodeState | undefined, becomes?: { state: NodeState; on: string }): NodeState =>
    becomes && frame >= wordFrame(words, becomes.on, fps, 10_000) ? becomes.state : base ?? "idle";
  const pulse = 0.75 + Math.sin(frame / 5) * 0.25;

  const fan = spec.fan;
  const fanTarget = fan ? byId.get(fan.to) : undefined;
  const fanAt = fan ? appearAt(fan.on, 0) : 0;

  return (
    <>
      <svg width={1080} height={1350} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
        {fan && fanTarget &&
          Array.from({ length: fan.count }, (_, i) => {
            const sx = area.left + 40 + (i / Math.max(1, fan.count - 1)) * (area.width - 80);
            const src: [number, number] = [sx, area.top - 30];
            const c = curveBetween(src, anchor(fanTarget, src));
            const color = stateColor(fan.state ?? "fail");
            const at = fanAt + i * 2;
            const draw = interpolate(frame - at, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            const [px, py] = pointAt(c, ((frame - at) / 24 + i * 0.13) % 1);
            return (
              <g key={`fan-${i}`} opacity={frame >= at ? 1 : 0}>
                <circle cx={src[0]} cy={src[1]} r={7} fill={COLOR.text} />
                <path d={pathD(c)} fill="none" stroke={color} strokeWidth={3} opacity={0.75} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - draw} style={{ filter: `drop-shadow(0 0 5px ${color})` }} />
                {draw >= 1 && <circle cx={px} cy={py} r={5} fill={color} />}
              </g>
            );
          })}
        {(spec.edges ?? []).map((e, i) => {
          const a = byId.get(e.from);
          const b = byId.get(e.to);
          if (!a || !b) return null;
          const c = curveBetween(anchor(a, toPx(b)), anchor(b, toPx(a)));
          const at = Math.max(appearAt(e.on, 0), nodeAt.get(e.from) ?? 0, nodeAt.get(e.to) ?? 0) + 4;
          const draw = interpolate(frame - at, [0, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const color = stateColor(stateOf(e.state, e.becomes));
          return (
            <g key={`edge-${i}`}>
              <path d={pathD(c)} fill="none" stroke={color} strokeWidth={4} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - draw} style={{ filter: `drop-shadow(0 0 8px ${color})` }} />
              {e.flow && draw >= 1 &&
                [0, 0.33, 0.66].map((off) => {
                  const [px, py] = pointAt(c, ((frame - at) / 30 + off) % 1);
                  return <circle key={off} cx={px} cy={py} r={7} fill={color} style={{ filter: `drop-shadow(0 0 8px ${color})` }} />;
                })}
            </g>
          );
        })}
      </svg>
      {spec.nodes.map((n) => {
        const [x, y] = toPx(n);
        const at = nodeAt.get(n.id) ?? 0;
        const pop = spring({ frame: frame - at, fps, config: { damping: 13, stiffness: 160 } });
        const state = stateOf(n.state, n.becomes);
        const color = stateColor(state);
        const glow = state === "hot" || state === "fail" ? pulse : 0.55;
        const isIcon = n.kind === "icon";
        return (
          <div
            key={n.id}
            style={{
              position: "absolute",
              left: x,
              top: y,
              transform: `translate(-50%, -50%) scale(${interpolate(pop, [0, 1], [0.6, 1])})`,
              opacity: pop,
              display: "flex",
              flexDirection: isIcon ? "column" : "row",
              alignItems: "center",
              justifyContent: "center",
              gap: isIcon ? 10 : 16,
              ...(isIcon
                ? {}
                : {
                    minWidth: BOX.w,
                    height: BOX.h,
                    padding: "0 26px",
                    boxSizing: "border-box",
                    border: `3px solid ${color}`,
                    borderRadius: 14,
                    background: `${COLOR.bgDeep}D9`,
                    boxShadow: `0 0 ${28 * glow}px ${color}88, inset 0 0 20px ${color}22`,
                  }),
            }}
          >
            {n.icon && <Icon name={n.icon} size={isIcon ? ICON_SIZE : 48} color={color} />}
            <div style={{ textAlign: isIcon ? "center" : "left" }}>
              <div style={{ fontFamily: FONT.mono, fontWeight: 700, fontSize: 28, letterSpacing: "0.08em", color, whiteSpace: "nowrap" }}>
                {n.label.toUpperCase()}
              </div>
              {n.sub && (
                <div style={{ fontFamily: FONT.mono, fontSize: 22, color: COLOR.textDim, whiteSpace: "nowrap" }}>{n.sub}</div>
              )}
            </div>
          </div>
        );
      })}
    </>
  );
};
