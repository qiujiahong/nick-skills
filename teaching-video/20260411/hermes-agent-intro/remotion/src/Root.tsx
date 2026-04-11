import {Composition} from 'remotion';
import {HermesAgentIntro, draftScenes, totalFrames} from './HermesAgentIntro';

export const Root = () => {
  return (
    <Composition
      id="HermesAgentIntro"
      component={HermesAgentIntro}
      durationInFrames={totalFrames}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{scenes: draftScenes}}
    />
  );
};
