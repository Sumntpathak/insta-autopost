import {Composition} from 'remotion';
import {LogoSting} from './LogoSting';
import {Scene1} from './Scene1';
import data from './scene1-data.json';
import {Story} from './Story';
import {AutomationReel} from './AutomationReel';

const GAP = 0.6;
const TAIL = 1.4;
const l1 = data.L1a;
const l2 = data.L2a;

// ShipStackStory: the earlier 15 s launch cut. Scene1Sample: motion sample for "View From the Top", scenes 1-2.
export const Root: React.FC = () => (
  <>
    <Composition id="LogoSting" component={LogoSting} durationInFrames={120} fps={30} width={1080} height={1920} defaultProps={{square: false}} />
    <Composition id="LogoSting4x5" component={LogoSting} durationInFrames={120} fps={30} width={1080} height={1350} defaultProps={{square: true}} />
    <Composition id="LogoStingSquare" component={LogoSting} durationInFrames={120} fps={30} width={1080} height={1080} defaultProps={{square: true}} />
    <Composition id="AutomationReel" component={AutomationReel} durationInFrames={450} fps={30} width={1080} height={1920} defaultProps={{episode: 1}} />
    <Composition id="ShipStackStory" component={Story} durationInFrames={450} fps={30} width={1080} height={1920} />
    <Composition id="Scene1Sample" component={Scene1} fps={30} width={1080} height={1920}
      durationInFrames={Math.ceil((l1.duration + GAP + l2.duration + TAIL) * 30)}
      defaultProps={{line1: l1.file, line2: l2.file, line1Dur: l1.duration, line2Dur: l2.duration, gap: GAP,
        words1: l1.words, words2: l2.words}} />
  </>
);
