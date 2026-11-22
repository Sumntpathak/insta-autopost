// node render.mjs [--still FRAME out.png]   (trailer: full edit, 1920x1080, 30 fps)
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';
import {existsSync} from 'node:fs';
const local = process.env.REMOTION_BROWSER || '/opt/pw-browsers/chromium_headless_shell';
const browserExecutable = existsSync(local) ? local : undefined;
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id: process.env.COMP || 'Video', browserExecutable});
const i = process.argv.indexOf('--still');
if (i > -1) {
  await renderStill({serveUrl, composition, frame: Number(process.argv[i + 1]), output: process.argv[i + 2], browserExecutable});
} else {
  await renderMedia({serveUrl, composition, codec: 'h264', audioCodec: 'aac', outputLocation: process.env.OUT || 'out/youtube-edit.mp4',
    browserExecutable, pixelFormat: 'yuv420p', crf: 18});
}
console.log('done');
