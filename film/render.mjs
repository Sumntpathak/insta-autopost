// Render the story film:  node render.mjs [--still FRAME out.png]
// Uses the pre-installed Chromium headless shell; output passes reels/verify.py (1080x1920, 30 fps, 15 s, AAC).
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';

const browserExecutable = process.env.REMOTION_BROWSER || '/opt/pw-browsers/chromium_headless_shell';
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id: 'ShipStackStory', browserExecutable});
const i = process.argv.indexOf('--still');
if (i > -1) {
  const frame = Number(process.argv[i + 1]);
  const output = process.argv[i + 2];
  await renderStill({serveUrl, composition, frame, output, browserExecutable});
  console.log(`Wrote ${output}`);
} else {
  const outputLocation = 'out/shipstack-story.mp4';
  await renderMedia({serveUrl, composition, codec: 'h264', audioCodec: 'aac', outputLocation, browserExecutable,
    pixelFormat: 'yuv420p', crf: 18});
  console.log(`Wrote ${outputLocation}`);
}
