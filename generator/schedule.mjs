// Builds ../schedule.json from data/posts.json: two slots a day (morning, evening).
// Usage: node schedule.mjs <first-date YYYY-MM-DD> <first-slot morning|evening> [skip-id ...]
// Journaled posts and any extra IDs supplied on the command line are omitted.
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const [firstDate, firstSlot = "morning", ...skip] = process.argv.slice(2);
if (!/^\d{4}-\d{2}-\d{2}$/.test(firstDate ?? "") || !["morning", "evening"].includes(firstSlot)) {
  console.error("usage: node schedule.mjs 2026-11-04 evening [S001]");
  process.exit(1);
}

const posted = JSON.parse(readFileSync(path.join(here, "..", "posted.json"), "utf8"));
const excluded = new Set([...posted.filter((p) => p.instagram).map((p) => p.id), ...skip]);
const posts = JSON.parse(readFileSync(path.join(here, "data", "posts.json"), "utf8"))
  .filter((p) => !excluded.has(p.id));
const missing = posts.flatMap((p) =>
  Array.from({ length: 6 }, (_, i) => `images/${p.id}_${i + 1}.jpg`).filter((f) => !existsSync(path.join(here, "..", f))),
);
if (missing.length) {
  console.error(`render first, missing ${missing.length} images, e.g. ${missing[0]}`);
  process.exit(1);
}

const caption = (p) => `${p.caption}\n\n${p.hashtags.map((h) => `#${h}`).join(" ")}`;
let date = new Date(`${firstDate}T00:00:00Z`);
let slot = firstSlot;
const schedule = posts.map((p) => {
    const entry = {
      date: date.toISOString().slice(0, 10),
      slot,
      id: p.id,
      images: Array.from({ length: 6 }, (_, i) => `images/${p.id}_${i + 1}.jpg`),
      caption: caption(p),
    };
    if (slot === "morning") slot = "evening";
    else {
      slot = "morning";
      date = new Date(date.getTime() + 86_400_000);
    }
    return entry;
  });

writeFileSync(path.join(here, "..", "schedule.json"), JSON.stringify(schedule, null, 2) + "\n");
if (schedule.length) {
  console.log(`scheduled ${schedule.length} posts: ${schedule[0].date} ${schedule[0].slot} -> ${schedule.at(-1).date} ${schedule.at(-1).slot}`);
} else {
  console.log("No unpublished posts to schedule.");
}
