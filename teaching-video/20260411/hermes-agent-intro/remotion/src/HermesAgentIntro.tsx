import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {scenes} from './timing.generated';

type Scene = {
  id: string;
  title: string;
  durationSec?: number;
  estimatedDurationSec?: number;
  audioFile: string;
  asset: string;
  hasAudio?: boolean;
};

export const draftScenes = scenes as Scene[];

const fps = 30;
const sceneFrames = (scene: Scene) => Math.round((scene.durationSec ?? scene.estimatedDurationSec ?? 20) * fps);
export const totalFrames = draftScenes.reduce((sum, scene) => sum + sceneFrames(scene), 0);

const tags: Record<string, string[]> = {
  'scene-01': ['长期同事', '记忆', 'Skills', '远程运行'],
  'scene-02': ['重复工作多', '想沉淀 skill', '需要多入口'],
  'scene-03': ['反复解释背景', '记住偏好', '流程可复用'],
  'scene-04': ['记忆', 'Skills', '跨平台入口', '远程运行'],
  'scene-05': ['本机/VPS', '国内可用模型', '内部 endpoint', '现有 IM'],
  'scene-06': ['跑通 CLI', '配置模型', '选重复任务', '跑 2-3 次', '再接 IM'],
  'scene-07': ['低风险', '高重复', '先跑闭环', '再扩大权限'],
};

const SceneSlide = ({scene}: {scene: Scene}) => {
  const frame = useCurrentFrame();
  const {fps: compositionFps} = useVideoConfig();
  const enter = spring({frame, fps: compositionFps, config: {damping: 18, stiffness: 90}});
  const imageScale = interpolate(frame, [0, sceneFrames(scene)], [1.02, 1.08], {extrapolateRight: 'clamp'});
  const titleY = interpolate(enter, [0, 1], [30, 0]);

  return (
    <AbsoluteFill
      style={{
        background: '#f7fbfa',
        color: '#10202a',
        fontFamily: 'Inter, PingFang SC, Arial, sans-serif',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 52,
          border: '1px solid rgba(32, 91, 102, 0.14)',
          background: 'linear-gradient(135deg, #fafffd 0%, #eef8f6 48%, #f4f8ff 100%)',
          borderRadius: 8,
          overflow: 'hidden',
        }}
      />
      <Img
        src={staticFile(scene.asset)}
        style={{
          position: 'absolute',
          left: 96,
          top: 152,
          width: 1220,
          height: 686,
          objectFit: 'cover',
          borderRadius: 8,
          boxShadow: '0 24px 80px rgba(20, 72, 92, 0.18)',
          transform: `scale(${imageScale})`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          right: 112,
          top: 178,
          width: 390,
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
          transform: `translateY(${titleY}px)`,
          opacity: enter,
        }}
      >
        <div style={{fontSize: 30, color: '#31958d', fontWeight: 700}}>Hermes Agent 入门</div>
        <div style={{fontSize: 54, lineHeight: 1.08, fontWeight: 800}}>{scene.title}</div>
        <div style={{height: 2, width: 168, background: '#6cc7bd'}} />
        <div style={{display: 'flex', flexWrap: 'wrap', gap: 12}}>
          {(tags[scene.id] ?? []).map((tag, index) => {
            const tagEnter = interpolate(frame, [8 + index * 6, 22 + index * 6], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            return (
              <span
                key={tag}
                style={{
                  opacity: tagEnter,
                  transform: `translateY(${(1 - tagEnter) * 10}px)`,
                  border: '1px solid rgba(49, 149, 141, 0.22)',
                  borderRadius: 8,
                  padding: '10px 14px',
                  fontSize: 24,
                  background: 'rgba(255,255,255,0.82)',
                  color: '#205b66',
                  fontWeight: 650,
                }}
              >
                {tag}
              </span>
            );
          })}
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 112,
          bottom: 86,
          fontSize: 24,
          color: '#64838c',
        }}
      >
        简洁科技风 · 中文教学视频 · 约 3 分钟
      </div>
      <div
        style={{
          position: 'absolute',
          right: 112,
          bottom: 86,
          fontSize: 22,
          color: '#82a2aa',
        }}
      >
        {scene.id}
      </div>
      {scene.hasAudio ? <Audio src={staticFile(scene.audioFile)} /> : null}
    </AbsoluteFill>
  );
};

export const HermesAgentIntro = ({scenes}: {scenes: Scene[]}) => {
  let start = 0;
  return (
    <AbsoluteFill>
      {scenes.map((scene) => {
        const duration = sceneFrames(scene);
        const from = start;
        start += duration;
        return (
          <Sequence key={scene.id} from={from} durationInFrames={duration}>
            <SceneSlide scene={scene} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
