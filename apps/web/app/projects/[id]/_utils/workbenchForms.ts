import type { Dispatch, SetStateAction } from "react";
import type {
  ProjectArtifactStatus,
  ProjectCharacterSnapshot,
  ProjectCopywriting,
  ProjectEpisodeContent,
  ProjectEpisodeOutline,
  ProjectEpisodeScript,
  ProjectStoryboardShot,
  ProjectStoryOutline,
  ProjectSummary,
  ProjectWorldSnapshot
} from "@/lib/api";
import type {
  CharacterSnapshotForm,
  CopywritingForm,
  EpisodeContentForm,
  EpisodeOutlineForm,
  EpisodeScriptForm,
  ProjectForm,
  ShotForm,
  Stage,
  StoryOutlineForm,
  WorldSnapshotEntryForm,
  WorkspaceMode,
  WorldSnapshotForm
} from "./workbenchTypes";

export const emptyProjectForm: ProjectForm = {
  title: "",
  idea: "",
  target_platform: "",
  genre: "",
  episode_count: "20",
  episode_duration: "1",
  target_audience: "",
  style: "",
  remark: ""
};

export const emptyWorldSnapshotForm: WorldSnapshotForm = {
  name: "",
  genre: "",
  era_background: "",
  world_rules: "",
  organizations: "",
  locations: "",
  social_structure: "",
  taboo_or_constraints: "",
  tone_style: "",
  summary: "",
  entries: [],
  snapshot_content: "",
  entry_snapshot_content: ""
};

export const emptyCharacterSnapshotForm: CharacterSnapshotForm = {
  name: "",
  gender: "女",
  role_type: "",
  identity: "",
  background: "",
  personality: "",
  goal: "",
  motivation: "",
  secret: "",
  conflict_points: "",
  relationship_notes: "",
  speech_style: "",
  catchphrases: "",
  emotional_arc: "",
  story_function: "",
  image_keywords: "",
  snapshot_content: "",
  visual_description: "",
  reference_image_url: "",
  reference_local_path: ""
};

export const emptyStoryForm: StoryOutlineForm = {
  logline: "",
  story_background: "",
  core_conflict: "",
  main_goal: "",
  story_start: "",
  plot_structure: "",
  reversals: "",
  emotion_curve: "",
  foreshadowing: "",
  character_arcs: "",
  ending_direction: "",
  pacing_advice: "",
  capacity_advice: "",
  notes: "",
  status: "draft"
};

export const emptyEpisodeForm: EpisodeOutlineForm = {
  title: "",
  synopsis: "",
  hook: "",
  conflict: "",
  reversal: "",
  cliffhanger: "",
  duration_minutes: "",
  status: "draft"
};

export const emptyContentForm: EpisodeContentForm = {
  title: "",
  detailed_content: "",
  chapter_summary: "",
  hook: "",
  key_beats: "",
  previous_context_summary: "",
  quality_check_notes: "",
  status: "draft"
};

export const emptyScriptForm: EpisodeScriptForm = {
  revision: null,
  title: "",
  scenes: []
};

export const emptyShotForm: ShotForm = {
  shot_no: "1",
  scene: "",
  visual_prompt: "",
  camera: "",
  duration_seconds: "",
  dialogue_or_voiceover: "",
  status: "draft"
};

export const emptyCopyForm: CopywritingForm = {
  subtitles: "",
  platform_title: "",
  platform_description: "",
  publish_copy: "",
  status: "draft"
};

export function projectToForm(project: ProjectSummary): ProjectForm {
  return {
    title: project.title,
    idea: project.idea,
    target_platform: project.target_platform || "",
    genre: project.genre || "",
    episode_count: String(project.episode_count),
    episode_duration: String(project.episode_duration),
    target_audience: project.target_audience || "",
    style: project.style || "",
    remark: project.remark || ""
  };
}

export function worldSnapshotToForm(snapshot: ProjectWorldSnapshot): WorldSnapshotForm {
  const content = parseSnapshot(snapshot.snapshot_content);
  return {
    name: snapshot.name,
    genre: snapshot.genre,
    era_background: snapshotField(content, "era_background"),
    world_rules: snapshotField(content, "world_rules"),
    organizations: snapshotField(content, "organizations"),
    locations: snapshotField(content, "locations"),
    social_structure: snapshotField(content, "social_structure"),
    taboo_or_constraints: snapshotField(content, "taboo_or_constraints"),
    tone_style: snapshotField(content, "tone_style"),
    summary: snapshotField(content, "summary"),
    entries: parseWorldSnapshotEntries(snapshot.entry_snapshot_content),
    snapshot_content: snapshot.snapshot_content,
    entry_snapshot_content: snapshot.entry_snapshot_content
  };
}

export function worldSnapshotFormToPayload(form: WorldSnapshotForm) {
  const baseContent = parseSnapshot(form.snapshot_content) ?? {};
  const nextContent = {
    ...baseContent,
    name: form.name,
    genre: form.genre,
    era_background: form.era_background,
    world_rules: form.world_rules,
    organizations: form.organizations,
    locations: form.locations,
    social_structure: form.social_structure,
    taboo_or_constraints: form.taboo_or_constraints,
    tone_style: form.tone_style,
    summary: form.summary
  };
  const originalEntries = parseSnapshotArray(form.entry_snapshot_content);
  const nextEntries = form.entries.map((entry, index) => ({
    ...(originalEntries[index] ?? {}),
    title: entry.title,
    entry_type: entry.entry_type,
    keywords: entry.keywords,
    content: entry.content,
    applicable_scope: entry.applicable_scope,
    priority: Number.isFinite(Number(entry.priority)) ? Number(entry.priority) : 0,
    status: entry.status
  }));

  return {
    name: form.name,
    genre: form.genre,
    snapshot_content: JSON.stringify(nextContent),
    entry_snapshot_content: JSON.stringify(nextEntries)
  };
}

export function characterSnapshotToForm(snapshot: ProjectCharacterSnapshot): CharacterSnapshotForm {
  const content = parseSnapshot(snapshot.snapshot_content);
  return {
    name: snapshot.name,
    gender: snapshot.gender,
    role_type: snapshot.role_type,
    identity: snapshotField(content, "identity"),
    background: snapshotField(content, "background"),
    personality: snapshotField(content, "personality"),
    goal: snapshotField(content, "goal"),
    motivation: snapshotField(content, "motivation"),
    secret: snapshotField(content, "secret"),
    conflict_points: snapshotField(content, "conflict_points"),
    relationship_notes: snapshotField(content, "relationship_notes"),
    speech_style: snapshotField(content, "speech_style"),
    catchphrases: snapshotField(content, "catchphrases"),
    emotional_arc: snapshotField(content, "emotional_arc"),
    story_function: snapshotField(content, "story_function"),
    image_keywords: localizeCharacterImageKeywords(snapshotField(content, "image_keywords")),
    snapshot_content: snapshot.snapshot_content,
    visual_description: snapshot.visual_description || snapshotField(content, "visual_description"),
    reference_image_url: snapshot.reference_image_url || "",
    reference_local_path: snapshot.reference_local_path || ""
  };
}

export function characterSnapshotFormToPayload(form: CharacterSnapshotForm) {
  const baseContent = parseSnapshot(form.snapshot_content) ?? {};
  const nextContent = {
    ...baseContent,
    name: form.name,
    gender: form.gender,
    role_type: form.role_type,
    identity: form.identity,
    background: form.background,
    personality: form.personality,
    goal: form.goal,
    motivation: form.motivation,
    secret: form.secret,
    conflict_points: form.conflict_points,
    relationship_notes: form.relationship_notes,
    speech_style: form.speech_style,
    catchphrases: form.catchphrases,
    emotional_arc: form.emotional_arc,
    story_function: form.story_function,
    visual_description: form.visual_description,
    image_keywords: form.image_keywords
  };

  return {
    name: form.name,
    gender: form.gender,
    role_type: form.role_type,
    snapshot_content: JSON.stringify(nextContent),
    visual_description: toOptional(form.visual_description),
    reference_image_url: toOptional(form.reference_image_url),
    reference_local_path: toOptional(form.reference_local_path)
  };
}

export function storyOutlineToForm(outline: ProjectStoryOutline | null): StoryOutlineForm {
  if (!outline) return emptyStoryForm;
  return {
    logline: outline.logline || "",
    story_background: outline.story_background || "",
    core_conflict: outline.core_conflict || "",
    main_goal: outline.main_goal || "",
    story_start: outline.story_start || "",
    plot_structure: outline.plot_structure || "",
    reversals: outline.reversals || "",
    emotion_curve: outline.emotion_curve || "",
    foreshadowing: outline.foreshadowing || "",
    character_arcs: outline.character_arcs || "",
    ending_direction: outline.ending_direction || "",
    pacing_advice: outline.pacing_advice || "",
    capacity_advice: outline.capacity_advice || "",
    notes: outline.notes || "",
    status: outline.status
  };
}

export function episodeOutlineToForm(outline: ProjectEpisodeOutline | null): EpisodeOutlineForm {
  if (!outline) return emptyEpisodeForm;
  return {
    title: outline.title || "",
    synopsis: outline.synopsis || "",
    hook: outline.hook || "",
    conflict: outline.conflict || "",
    reversal: outline.reversal || "",
    cliffhanger: outline.cliffhanger || "",
    duration_minutes: outline.duration_minutes ? String(outline.duration_minutes) : "",
    status: outline.status
  };
}

export function episodeContentToForm(content: ProjectEpisodeContent | null): EpisodeContentForm {
  if (!content) return emptyContentForm;
  return {
    title: content.title || "",
    detailed_content: content.detailed_content || "",
    chapter_summary: content.chapter_summary || "",
    hook: content.hook || "",
    key_beats: content.key_beats || "",
    previous_context_summary: content.previous_context_summary || "",
    quality_check_notes: content.quality_check_notes || "",
    status: content.status
  };
}

export function episodeScriptToForm(script: ProjectEpisodeScript | null): EpisodeScriptForm {
  if (!script) return emptyScriptForm;
  return {
    revision: script.revision,
    title: script.title || "",
    manual_duration_seconds: script.manual_duration_seconds,
    scenes: script.scenes.map((scene) => ({
      id: scene.id,
      title: scene.title,
      location: scene.location,
      time_of_day: scene.time_of_day,
      interior_exterior: scene.interior_exterior,
      character_snapshot_ids: scene.character_snapshot_ids,
      manual_duration_seconds: scene.manual_duration_seconds,
      story_purpose: scene.story_purpose,
      blocks: scene.blocks.map((block) => ({
        id: block.id,
        block_type: block.block_type,
        character_snapshot_id: block.character_snapshot_id,
        temporary_speaker_name: block.temporary_speaker_name,
        content: block.content,
        emotion: block.emotion,
        performance_note: block.performance_note
      }))
    }))
  };
}

export function shotToForm(shot: ProjectStoryboardShot): ShotForm {
  return {
    shot_no: String(shot.shot_no),
    scene: shot.scene || "",
    visual_prompt: shot.visual_prompt || "",
    camera: shot.camera || "",
    duration_seconds: shot.duration_seconds ? String(shot.duration_seconds) : "",
    dialogue_or_voiceover: shot.dialogue_or_voiceover || "",
    status: shot.status === "pending_review" ? "needs_review" : shot.status
  };
}

export function copywritingToForm(copy: ProjectCopywriting | null): CopywritingForm {
  if (!copy) return emptyCopyForm;
  return {
    subtitles: copy.subtitles || "",
    platform_title: copy.platform_title || "",
    platform_description: copy.platform_description || "",
    publish_copy: copy.publish_copy || "",
    status: copy.status
  };
}

export function validateProject(form: ProjectForm, episodeCount: number, episodeDuration: number, totalDuration: number) {
  if (!form.idea.trim()) {
    return "请先输入短剧创意描述";
  }
  if (!Number.isInteger(episodeCount) || episodeCount <= 0) {
    return "集数必须是大于 0 的整数";
  }
  if (!Number.isFinite(episodeDuration) || episodeDuration <= 0) {
    return "单集时长必须大于 0 分钟";
  }
  if (episodeDuration > 2) {
    return "单集时长不能超过 2 分钟";
  }
  // 总时长是项目生成流程的强约束，超限时前端和后端都必须阻止保存。
  if (totalDuration > 240) {
    return "总时长不能超过 240 分钟，请减少集数或单集时长";
  }
  return "";
}

export function defaultStageForMode(mode: WorkspaceMode): Stage {
  if (mode === "storyText") return "story";
  if (mode === "production") return "script";
  return "settings";
}

export function replaceEpisodeOutline(current: ProjectEpisodeOutline[], next: ProjectEpisodeOutline) {
  const filtered = current.filter((outline) => outline.episode_no !== next.episode_no);
  return [...filtered, next].sort((a, b) => a.episode_no - b.episode_no);
}

export function replaceWorldSnapshot(current: ProjectWorldSnapshot[], next: ProjectWorldSnapshot) {
  const filtered = current.filter((snapshot) => snapshot.id !== next.id);
  return [...filtered, next].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
}

export function replaceCharacterSnapshot(current: ProjectCharacterSnapshot[], next: ProjectCharacterSnapshot) {
  const filtered = current.filter((snapshot) => snapshot.id !== next.id);
  return [...filtered, next].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
}

export function replaceShot(current: ProjectStoryboardShot[], next: ProjectStoryboardShot) {
  const filtered = current.filter((shot) => shot.id !== next.id);
  return [...filtered, next].sort((a, b) => a.shot_no - b.shot_no);
}

export function storyFormToPayload(form: StoryOutlineForm) {
  return {
    logline: toOptional(form.logline),
    story_background: toOptional(form.story_background),
    core_conflict: toOptional(form.core_conflict),
    main_goal: toOptional(form.main_goal),
    story_start: toOptional(form.story_start),
    plot_structure: toOptional(form.plot_structure),
    reversals: toOptional(form.reversals),
    emotion_curve: toOptional(form.emotion_curve),
    foreshadowing: toOptional(form.foreshadowing),
    character_arcs: toOptional(form.character_arcs),
    ending_direction: toOptional(form.ending_direction),
    pacing_advice: toOptional(form.pacing_advice),
    capacity_advice: toOptional(form.capacity_advice),
    notes: toOptional(form.notes),
    status: form.status
  };
}

export function nextShotNo(shots: ProjectStoryboardShot[]) {
  return shots.reduce((max, shot) => Math.max(max, shot.shot_no), 0) + 1;
}

export function countContentCharacters(content: string) {
  return Array.from(content).filter((char) => !/\s/.test(char)).length;
}

export function setProjectFormValue(field: keyof ProjectForm, value: string, setter: Dispatch<SetStateAction<ProjectForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

export function setWorldSnapshotFormValue(field: keyof WorldSnapshotForm, value: string, setter: Dispatch<SetStateAction<WorldSnapshotForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

export function setCharacterSnapshotFormValue(
  field: keyof CharacterSnapshotForm,
  value: string | "男" | "女",
  setter: Dispatch<SetStateAction<CharacterSnapshotForm>>
) {
  setter((current) => ({ ...current, [field]: value }));
}

export function setStoryFormValue(field: keyof StoryOutlineForm, value: string | ProjectArtifactStatus, setter: Dispatch<SetStateAction<StoryOutlineForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

export function setEpisodeFormValue(field: keyof EpisodeOutlineForm, value: string | ProjectArtifactStatus, setter: Dispatch<SetStateAction<EpisodeOutlineForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

export function setContentFormValue(field: keyof EpisodeContentForm, value: string | ProjectArtifactStatus, setter: Dispatch<SetStateAction<EpisodeContentForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

export function setShotFormValue(field: keyof ShotForm, value: string | ProjectArtifactStatus, setter: Dispatch<SetStateAction<ShotForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

export function setCopyFormValue(field: keyof CopywritingForm, value: string | ProjectArtifactStatus, setter: Dispatch<SetStateAction<CopywritingForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

export function toOptional(value: string) {
  const stripped = value.trim();
  return stripped || undefined;
}

export function toOptionalNumber(value: string) {
  if (!value.trim()) return undefined;
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : undefined;
}

export function artifactStatusLabel(status: ProjectArtifactStatus | "pending_review") {
  if (status === "confirmed") return "已确认";
  if (status === "pending_review") return "待确认";
  if (status === "needs_review") return "需要检查";
  return "草稿";
}

export function artifactStatusClass(status: ProjectArtifactStatus | "pending_review") {
  if (status === "confirmed") return "status-active";
  if (status === "needs_review") return "status-review";
  return "status-draft";
}

export function worldSnapshotSummary(snapshot: ProjectWorldSnapshot) {
  const content = parseSnapshot(snapshot.snapshot_content);
  if (content && typeof content.summary === "string" && content.summary.trim()) {
    return content.summary;
  }
  if (content && typeof content.world_rules === "string" && content.world_rules.trim()) {
    return content.world_rules;
  }
  return "已加载到项目的世界观副本。";
}

export function characterSnapshotSummary(snapshot: ProjectCharacterSnapshot) {
  const content = parseSnapshot(snapshot.snapshot_content);
  if (content && typeof content.identity === "string" && content.identity.trim()) {
    return content.identity;
  }
  if (content && typeof content.goal === "string" && content.goal.trim()) {
    return content.goal;
  }
  return "已加载到项目的角色副本。";
}

export function characterSnapshotImageUrl(snapshot: ProjectCharacterSnapshot) {
  if (snapshot.reference_image_url?.trim()) return snapshot.reference_image_url;
  return snapshotField(parseSnapshot(snapshot.snapshot_content), "turnaround_image_url");
}

function localizeCharacterImageKeywords(value: string) {
  const glossary: Record<string, string> = {
    "European medieval knight": "欧洲中世纪骑士",
    "dark green cloak": "深绿色斗篷",
    "leather armor": "皮甲",
    chainmail: "锁子甲",
    "grounded realism": "写实质感",
    "medieval herbalist": "中世纪草药师",
    "auburn braid": "红褐色长辫",
    "dark blue gown": "深蓝长袍",
    "leather satchel": "皮革挎包",
    "court intrigue": "宫廷权谋氛围",
    "Chinese primordial casual fantasy": "中国洪荒休闲奇幻",
    "mountain spirit": "山灵",
    "celadon robe": "青瓷色长袍",
    "gourd flask": "葫芦酒壶",
    "relaxed cultivator": "松弛感修行者",
    "Chinese fantasy innkeeper": "中国奇幻客栈掌柜",
    "peach blossom spirit": "桃花灵",
    "peach hanfu": "桃色汉服",
    "lively warm expression": "活泼温暖的神情",
    "casual myth": "轻松神话风格",
    "modern urban doctor": "现代都市医生",
    "East Asian male": "东亚男性",
    "charcoal bomber jacket": "炭灰色飞行夹克",
    "hospital ID": "医院工牌",
    "realistic wardrobe": "写实服装",
    "modern investigative journalist": "现代调查记者",
    "East Asian female": "东亚女性",
    "beige trench coat": "米色风衣",
    "canvas bag": "帆布包",
    "realistic urban style": "写实都市风格"
  };

  return value
    .split(",")
    .map((keyword) => glossary[keyword.trim()] || keyword.trim())
    .filter(Boolean)
    .join("、");
}

export function parseSnapshot(content: string): Record<string, unknown> | null {
  try {
    const parsed: unknown = JSON.parse(content);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
  } catch {
    return null;
  }
  return null;
}

function parseSnapshotArray(content: string): Array<Record<string, unknown>> {
  try {
    const parsed: unknown = JSON.parse(content);
    if (Array.isArray(parsed)) {
      return parsed.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object" && !Array.isArray(item));
    }
  } catch {
    return [];
  }
  return [];
}

function snapshotField(content: Record<string, unknown> | null, field: string) {
  const value = content?.[field];
  return typeof value === "string" ? value : "";
}

function snapshotNumberField(content: Record<string, unknown>, field: string) {
  const value = content[field];
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  if (typeof value === "string") return value;
  return "0";
}

function parseWorldSnapshotEntries(content: string): WorldSnapshotEntryForm[] {
  return parseSnapshotArray(content).map((entry) => ({
    title: snapshotField(entry, "title"),
    entry_type: (snapshotField(entry, "entry_type") || "其他") as WorldSnapshotEntryForm["entry_type"],
    keywords: snapshotField(entry, "keywords"),
    content: snapshotField(entry, "content"),
    applicable_scope: snapshotField(entry, "applicable_scope"),
    priority: snapshotNumberField(entry, "priority"),
    status: (snapshotField(entry, "status") || "active") as WorldSnapshotEntryForm["status"]
  }));
}

export function formatNumber(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}
