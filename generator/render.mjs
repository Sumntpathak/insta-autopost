// Renders every post in data/posts.json to ../images/<id>_<n>.jpg (1080x1350 JPEG).
// Usage: node render.mjs [ID ...]   (no ids = all posts; existing files are overwritten)
import { bundle } from "@remotion/bundler";
import { openBrowser, renderStill, selectComposition } from "@remotion/renderer";
import { readFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(here, "..", "images");
const SLIDES = 6;

const posts = JSON.parse(readFileSync(path.join(here, "data", "posts.json"), "utf8"));
const wanted = new Set(process.argv.slice(2));
const todo = wanted.size ? posts.filter((p) => wanted.has(p.id)) : posts;
if (!todo.length) throw new Error(`no matching posts for: ${[...wanted].join(", ")}`);

mkdirSync(outDir, { recursive: true });
console.log(`bundling...`);
const serveUrl = await bundle({ entryPoint: path.join(here, "src", "index.ts") });
const browser = await openBrowser("chrome");

try {
  for (const post of todo) {
    for (let slide = 0; slide < SLIDES; slide++) {
      const inputProps = { postId: post.id, slide };
      const composition = await selectComposition({ serveUrl, id: "Slide", inputProps, puppeteerInstance: browser });
      const output = path.join(outDir, `${post.id}_${slide + 1}.jpg`);
      await renderStill({
        composition,
        serveUrl,
        output,
        inputProps,
        imageFormat: "jpeg",
        jpegQuality: 90,
        puppeteerInstance: browser,
        overwrite: true,
      });
    }
    console.log(`rendered ${post.id} (${post.topic})`);
  }
} finally {
  await browser.close({ silent: true });
}
