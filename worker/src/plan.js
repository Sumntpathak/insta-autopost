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
