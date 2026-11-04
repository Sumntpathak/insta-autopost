// Validates post content against the slide layout limits before rendering.
// Usage: node validate.mjs [file ...]   (default: data/posts.json)
import { readFileSync } from "node:fs";

const ICONS = new Set(["phone", "server", "db", "user", "chip", "cache", "lock", "clock", "seat", "queue"]);
const STATES = new Set(["idle", "hot", "fail", "ok", "dim"]);
// Max visible characters (markup stripped) that fit each text slot.
const LIMIT = {
  coverHeadline: 52, headline: 46, storyBody: 190, body: 150,
  mapStory: 18, mapTech: 14, saveItem: 22, question: 42, option: 24,
  caption: 700, label: 12, sub: 18,
};

const visible = (s = "") => s.replace(/[*`]/g, "");
const files = process.argv.slice(2).length ? process.argv.slice(2) : ["data/posts.json"];
const errors = [];
const seenIds = new Set();
const seenTopics = new Set();

const checkLen = (where, text, max) => {
  if (typeof text !== "string" || !text.trim()) errors.push(`${where}: missing`);
  else if (visible(text).length > max) errors.push(`${where}: ${visible(text).length} chars > ${max} ("${visible(text)}")`);
};

const checkDiagram = (where, d) => {
  if (!d || !Array.isArray(d.nodes) || !d.nodes.length) return errors.push(`${where}: diagram needs nodes`);
  if (d.nodes.length > 4) errors.push(`${where}: ${d.nodes.length} nodes (max 4 on a phone screen)`);
  const ids = new Set(d.nodes.map((n) => n.id));
  d.nodes.forEach((n) => {
    checkLen(`${where}.node ${n.id}.label`, n.label, LIMIT.label);
    if (n.sub) checkLen(`${where}.node ${n.id}.sub`, n.sub, LIMIT.sub);
    if (!(n.x >= 12 && n.x <= 88)) errors.push(`${where}.node ${n.id}: x ${n.x} outside 12-88`);
    if (!(n.y >= 10 && n.y <= 88)) errors.push(`${where}.node ${n.id}: y ${n.y} outside 10-88`);
    if (n.icon && !ICONS.has(n.icon)) errors.push(`${where}.node ${n.id}: unknown icon ${n.icon}`);
    if (n.state && !STATES.has(n.state)) errors.push(`${where}.node ${n.id}: unknown state ${n.state}`);
  });
  // boxes on the same row need horizontal room (box >= 260px of a 960px area)
  const boxes = d.nodes.filter((n) => n.kind !== "icon");
  boxes.forEach((a, i) => boxes.slice(i + 1).forEach((b) => {
    if (Math.abs(a.y - b.y) < 30 && Math.abs(a.x - b.x) < 34) errors.push(`${where}: nodes ${a.id} and ${b.id} overlap (same row, x gap < 34)`);
  }));
  (d.edges ?? []).forEach((e) => {
    if (!ids.has(e.from) || !ids.has(e.to)) errors.push(`${where}: edge ${e.from}->${e.to} references a missing node`);
    if (e.state && !STATES.has(e.state)) errors.push(`${where}: edge state ${e.state}`);
  });
  if (d.fan) {
    if (!ids.has(d.fan.to)) errors.push(`${where}: fan target ${d.fan.to} missing`);
    if (!(d.fan.count >= 6 && d.fan.count <= 16)) errors.push(`${where}: fan count 6-16`);
    const t = d.nodes.find((n) => n.id === d.fan.to);
    if (t && t.y < 65) errors.push(`${where}: fan target y ${t.y} should be >= 65 so wires have room`);
  }
};

for (const file of files) {
  const posts = JSON.parse(readFileSync(file, "utf8"));
  if (!Array.isArray(posts)) { errors.push(`${file}: must be a JSON array`); continue; }
  for (const p of posts) {
    const w = `${file} ${p.id ?? "?"}`;
    if (!/^S\d{3}$/.test(p.id ?? "")) errors.push(`${w}: id must look like S001`);
    if (p.number !== Number(p.id?.slice(1))) errors.push(`${w}: number must match id`);
    if (seenIds.has(p.id)) errors.push(`${w}: duplicate id`);
    seenIds.add(p.id);
    const topicKey = (p.topic ?? "").toLowerCase();
    if (seenTopics.has(topicKey)) errors.push(`${w}: duplicate topic ${p.topic}`);
    seenTopics.add(topicKey);
    checkLen(`${w}.topic`, p.topic, 24);
    checkLen(`${w}.cover.headline`, p.cover?.headline, LIMIT.coverHeadline);
    checkLen(`${w}.story.headline`, p.story?.headline, LIMIT.headline);
    checkLen(`${w}.story.body`, p.story?.body, LIMIT.storyBody);
    if (!Array.isArray(p.story?.mapping) || p.story.mapping.length < 2 || p.story.mapping.length > 3) errors.push(`${w}: story.mapping needs 2-3 rows`);
    (p.story?.mapping ?? []).forEach((m, i) => {
      checkLen(`${w}.mapping[${i}].story`, m.story, LIMIT.mapStory);
      checkLen(`${w}.mapping[${i}].tech`, m.tech, LIMIT.mapTech);
    });
    for (const k of ["trap", "fix"]) {
      checkLen(`${w}.${k}.headline`, p[k]?.headline, LIMIT.headline);
      checkLen(`${w}.${k}.body`, p[k]?.body, LIMIT.body);
      checkDiagram(`${w}.${k}`, p[k]?.diagram);
    }
    if (p.save?.items?.length !== 4) errors.push(`${w}: save.items needs exactly 4`);
    (p.save?.items ?? []).forEach((it, i) => checkLen(`${w}.save[${i}]`, it, LIMIT.saveItem));
    checkLen(`${w}.cta.question`, p.cta?.question, LIMIT.question);
    if (p.cta?.options?.length !== 2) errors.push(`${w}: cta.options needs exactly 2`);
    (p.cta?.options ?? []).forEach((o, i) => checkLen(`${w}.cta.options[${i}]`, o, LIMIT.option));
    checkLen(`${w}.caption`, p.caption, LIMIT.caption);
    if (!Array.isArray(p.hashtags) || p.hashtags.length < 3 || p.hashtags.length > 5) errors.push(`${w}: 3-5 hashtags (Instagram caps hashtags; more looks spammy)`);
    (p.hashtags ?? []).forEach((h) => { if (!/^[a-z0-9]+$/.test(h)) errors.push(`${w}: hashtag "${h}" must be lowercase a-z0-9, no #`); });
  }
}

if (errors.length) {
  console.error(`${errors.length} problem(s):\n  - ${errors.join("\n  - ")}`);
  process.exit(1);
}
console.log(`OK: ${seenIds.size} posts valid (${files.join(", ")})`);
