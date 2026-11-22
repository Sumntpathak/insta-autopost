import {Composition} from 'remotion';
import {TOTAL, Video} from './Video';
import {useFonts} from './fonts';
import {FPS} from './brand';
const Main = () => { useFonts(); return <Video />; };
export const Root = () => <Composition id="Video" component={Main} durationInFrames={TOTAL} fps={FPS} width={1920} height={1080} />;
