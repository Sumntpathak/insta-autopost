import {Composition} from 'remotion';
import {Trailer, FPS, TOTAL} from './Trailer';
export const Root = () => (
  <Composition id="Trailer" component={Trailer} durationInFrames={TOTAL} fps={FPS} width={1920} height={1080} />
);
