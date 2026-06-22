import type { ProjectArtifactStatus, ProjectEpisodeScriptPayload, WorldEntryStatus, WorldEntryType } from "@/lib/api";

export type Stage = "settings" | "world" | "characters" | "story" | "episodes" | "content" | "script" | "storyboard" | "copywriting";
export type WorkspaceGroupKey = "projectAssets" | "storyText" | "production";
export type WorkspaceMode = "landing" | WorkspaceGroupKey;
export type ReferenceTab = "settings" | "characters" | "style" | "inspiration";

export type ProjectForm = {
  title: string;
  idea: string;
  target_platform: string;
  genre: string;
  episode_count: string;
  episode_duration: string;
  target_audience: string;
  style: string;
  remark: string;
};

export type WorldSnapshotForm = {
  name: string;
  genre: string;
  era_background: string;
  world_rules: string;
  organizations: string;
  locations: string;
  social_structure: string;
  taboo_or_constraints: string;
  tone_style: string;
  summary: string;
  entries: WorldSnapshotEntryForm[];
  snapshot_content: string;
  entry_snapshot_content: string;
};

export type WorldSnapshotEntryForm = {
  title: string;
  entry_type: WorldEntryType;
  keywords: string;
  content: string;
  applicable_scope: string;
  priority: string;
  status: WorldEntryStatus;
};

export type CharacterSnapshotForm = {
  name: string;
  gender: "男" | "女";
  role_type: string;
  identity: string;
  background: string;
  personality: string;
  goal: string;
  motivation: string;
  secret: string;
  conflict_points: string;
  relationship_notes: string;
  speech_style: string;
  catchphrases: string;
  emotional_arc: string;
  story_function: string;
  image_keywords: string;
  snapshot_content: string;
  visual_description: string;
  reference_image_url: string;
  reference_local_path: string;
};

export type StoryOutlineForm = {
  logline: string;
  story_background: string;
  core_conflict: string;
  main_goal: string;
  story_start: string;
  plot_structure: string;
  reversals: string;
  emotion_curve: string;
  foreshadowing: string;
  character_arcs: string;
  ending_direction: string;
  pacing_advice: string;
  capacity_advice: string;
  notes: string;
  status: ProjectArtifactStatus;
};

export type EpisodeOutlineForm = {
  title: string;
  synopsis: string;
  hook: string;
  conflict: string;
  reversal: string;
  cliffhanger: string;
  duration_minutes: string;
  status: ProjectArtifactStatus;
};

export type EpisodeContentForm = {
  title: string;
  detailed_content: string;
  chapter_summary: string;
  hook: string;
  key_beats: string;
  previous_context_summary: string;
  quality_check_notes: string;
  status: ProjectArtifactStatus;
};

export type EpisodeScriptForm = ProjectEpisodeScriptPayload;

export type ShotForm = {
  shot_no: string;
  scene: string;
  visual_prompt: string;
  camera: string;
  duration_seconds: string;
  dialogue_or_voiceover: string;
  status: ProjectArtifactStatus;
};

export type CopywritingForm = {
  subtitles: string;
  platform_title: string;
  platform_description: string;
  publish_copy: string;
  status: ProjectArtifactStatus;
};

export const workspaceGroups: Array<{
  key: WorkspaceGroupKey;
  title: string;
  description: string;
  defaultStage: Stage;
  stages: Array<{ key: Stage; label: string }>;
}> = [
  {
    key: "projectAssets",
    title: "项目资料 / 资产",
    description: "维护基础信息、世界观和角色，作为故事文本与短剧制作共用的项目上下文。",
    defaultStage: "settings",
    stages: [
      { key: "settings", label: "基础信息" },
      { key: "world", label: "世界观" },
      { key: "characters", label: "角色" }
    ]
  },
  {
    key: "storyText",
    title: "故事文本",
    description: "把项目写成可读的故事文本，包含整体结构、分集结构和单集故事正文。",
    defaultStage: "story",
    stages: [
      { key: "story", label: "故事大纲" },
      { key: "episodes", label: "分集大纲" },
      { key: "content", label: "单集故事正文" }
    ]
  },
  {
    key: "production",
    title: "短剧制作",
    description: "沿用故事文本和项目资产，把每集单集故事正文转换为脚本、分镜、字幕和平台文案。",
    defaultStage: "script",
    stages: [
      { key: "script", label: "剧本" },
      { key: "storyboard", label: "分镜" },
      { key: "copywriting", label: "字幕与文案" }
    ]
  }
];

export const episodeAiActions = ["正文创作", "续写", "润色", "撤销润色", "摘要", "一致性质检"];
export const productionAiActions = ["钩子提取"];

export const referenceTabs: Array<{ key: ReferenceTab; label: string }> = [
  { key: "settings", label: "设定" },
  { key: "characters", label: "角色" },
  { key: "style", label: "文风" },
  { key: "inspiration", label: "灵感" }
];
