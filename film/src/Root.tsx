import {Composition} from 'remotion';
import {Story} from './Story';

// 15 s at 30 fps = 450 frames: passes reels/verify.py, so it can go through the guarded publisher.
export const Root: React.FC = () => (
  <Composition id="ShipStackStory" component={Story} durationInFrames={450} fps={30} width={1080} height={1920} />
);
