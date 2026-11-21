// Render the story film:  node render.mjs [--still FRAME out.png]
// Uses the pre-installed Chromium headless shell; output passes reels/verify.py (1080x1920, 30 fps, 15 s, AAC).
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';

import {existsSync, readFileSync} from 'node:fs';
// Local sandbox ships a headless shell; on CI leave undefined so Remotion downloads its own.
const local = process.env.REMOTION_BROWSER || '/opt/pw-browsers/chromium_headless_shell';
const browserExecutable = existsSync(local) ? local : undefined;
const inputProps = {episode: Number(process.env.EPISODE || 1), ...(process.env.MUSIC ? {music: process.env.MUSIC, keyGain: Number(process.env.KEY_GAIN || 0.35), musicVolume: Number(process.env.MUSIC_VOL || 0.5)} : {})};
if (process.env.PROPS_FILE) Object.assign(inputProps, JSON.parse(readFileSync(process.env.PROPS_FILE, 'utf8')));
const id = process.env.COMP || 'ShipStackStory';
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id, browserExecutable, inputProps});
const i = process.argv.indexOf('--still');
if (i > -1) {
  const frame = Number(process.argv[i + 1]);
  const output = process.argv[i + 2];
  await renderStill({serveUrl, composition, inputProps, frame, output, browserExecutable});
  console.log(`Wrote ${output}`);
} else {
  const outputLocation = process.env.OUT || 'out/shipstack-story.mp4';
  await renderMedia({serveUrl, composition, inputProps, codec: 'h264', audioCodec: 'aac', outputLocation, browserExecutable,
    pixelFormat: 'yuv420p', crf: 18});
  console.log(`Wrote ${outputLocation}`);
}
