// Pure due-slot logic. Mirrors reels/shipstack/schedule.py due(): the earliest unposted slot whose time has
// passed by less than STALE_MS. The workflow re-checks everything (and enforces the posting guard); this only
// decides whether a run is worth starting.
export const STALE_MS = 3 * 60 * 60 * 1000;

export function slotTime(slot) {
  return Date.parse(`${slot.date}T${slot.time}:00+05:30`);   // calendar times are IST
}

export function dueSlot(calendar, posts, nowMs) {
  if (!calendar || calendar.paused) return null;
  for (const slot of calendar.slots ?? []) {
    const at = slotTime(slot);
    if (at <= nowMs && nowMs < at + STALE_MS && !(slot.id in posts)) return slot;
  }
  return null;
}

// Mirrors reels/guard.py blocked(): at least MIN_GAP_MS since the last non-story post (any pipeline in the journal) and at most
// DAILY_CAP posts per IST day. Lets the Worker wait quietly instead of starting runs that the workflow would only refuse.
export const MIN_GAP_MS = 60 * 60 * 1000;
export const DAILY_CAP = 12;
const IST_MS = 5.5 * 60 * 60 * 1000;

export function guardBlock(posts, nowMs) {
  const times = Object.values(posts)
    .filter((p) => p.kind !== 'story')
    .map((p) => Date.parse(p.published_at || p.attempted_at || ''))
    .filter((t) => !Number.isNaN(t));
  if (times.length) {
    const last = Math.max(...times);
    if (nowMs - last < MIN_GAP_MS) return `last post ${Math.round((nowMs - last) / 60000)} min ago`;
  }
  const day = (t) => new Date(t + IST_MS).toISOString().slice(0, 10);
  const today = times.filter((t) => day(t) === day(nowMs)).length;
  return today >= DAILY_CAP ? `${today} posts today` : null;
}
