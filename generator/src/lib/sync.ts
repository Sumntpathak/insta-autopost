import type { Word } from "./types";

const normalise = (s: string): string => s.toLowerCase().replace(/[^a-z0-9]/g, "");

/**
 * Frame (local to the step) at which `needle` is spoken, so visual beats land on
 * the word: wordFrame(words, "TTL", fps). `occurrence` picks the nth match (0-based).
 * Returns `fallback` when there is no timing yet or the word is not found.
 */
export const wordFrame = (
  words: Word[],
  needle: string,
  fps: number,
  fallback = 0,
  occurrence = 0,
): number => {
  const target = normalise(needle);
  const hits = words.filter((w) => normalise(w.text).startsWith(target));
  const hit = hits[occurrence];
  return hit ? Math.round(hit.start * fps) : fallback;
};
