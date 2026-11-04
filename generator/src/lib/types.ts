export type Word = { text: string; start: number; end: number };

export type NodeState = "idle" | "hot" | "fail" | "ok" | "dim";

export type IconName = "phone" | "server" | "db" | "user" | "chip" | "cache" | "lock" | "clock" | "seat" | "queue";

export type DiagramNode = {
  id: string;
  label: string;
  sub?: string;
  icon?: IconName;
  kind?: "box" | "icon";
  /** centre in percent of the diagram area (0-100) */
  x: number;
  y: number;
  state?: NodeState;
  on?: string;
  becomes?: { state: NodeState; on: string };
};

export type DiagramEdge = {
  from: string;
  to: string;
  state?: NodeState;
  flow?: boolean;
  on?: string;
  becomes?: { state: NodeState; on: string };
};

export type Diagram = {
  nodes: DiagramNode[];
  edges?: DiagramEdge[];
  fan?: { to: string; count: number; state?: NodeState; on?: string };
};

/** One carousel post = 6 slides: cover, story, trap, fix, save, cta. */
export type Post = {
  /** "S001" */
  id: string;
  number: number;
  topic: string;
  /** cover headline; *stars* = yellow highlight, `ticks` = code chip. Cover shows trap.diagram. */
  cover: { headline: string };
  /** the desi analogy: who/what in the story maps to which component */
  story: { headline: string; body: string; mapping: Array<{ story: string; tech: string }> };
  trap: { headline: string; body: string; diagram: Diagram };
  fix: { headline: string; body: string; diagram: Diagram };
  /** interview cheat sheet, 4 items of <= 4 words */
  save: { items: string[] };
  cta: { question: string; options: [string, string] };
  /** caption body without hashtags */
  caption: string;
  /** <= 5 hashtags, without '#' */
  hashtags: string[];
};
