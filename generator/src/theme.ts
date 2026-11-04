import { loadFont as loadDisplay } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";

const display = loadDisplay("normal", { weights: ["500", "700"], subsets: ["latin"] });
const mono = loadMono("normal", { weights: ["500", "700"], subsets: ["latin"] });

/** Instagram feed carousel: 4:5 portrait. */
export const VIDEO = { width: 1080, height: 1350, fps: 30 } as const;

/** Keep content inside this; the profile grid crops ~34px off each side (3:4 preview). */
export const SAFE = { left: 80, right: 1000, top: 60, bottom: 1290 } as const;

/** Default diagram area. Slides pass their own `area` to <Diagram>. */
export const BODY = { left: 60, top: 560, width: 960, height: 460 } as const;

export type Area = { left: number; top: number; width: number; height: number };

export const TIMING = { wordsPerSecond: 1.8 } as const;

/** Blueprint series palette: yellow = live/highlight, red = failure, green = the fix. */
export const COLOR = {
  bg: "#061433",
  bgDeep: "#030B22",
  bgRaised: "#0B1E47",
  grid: "#16306A",
  text: "#FFFFFF",
  textDim: "#8EA2CC",
  accent: "#FFC83D",
  healthy: "#9CC3FF",
  waiting: "#FFC83D",
  failed: "#FF4F6D",
  confirmed: "#4ADE80",
} as const;

export const FONT = {
  display: display.fontFamily,
  mono: mono.fontFamily,
} as const;

export const BRAND = {
  handle: "@shipstack_",
  series: "SYSTEM DESIGN",
  slides: 6,
} as const;
