const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type ModelConfigPayload = {
  config_type: "text" | "image";
  provider_mode?: "preset" | "custom";
  provider_preset?: string;
  provider_name: string;
  api_base_url: string;
  api_key: string;
  model_name: string;
  image_size?: string;
  endpoint_path?: string;
  supports_reference_image?: boolean;
  remark?: string;
  enabled?: boolean;
};

export type ModelConfig = {
  id: string;
  config_type: "text" | "image";
  provider_mode: "preset" | "custom";
  provider_preset?: string;
  provider_name: string;
  api_base_url: string;
  api_key_masked: string;
  model_name: string;
  image_size?: string;
  endpoint_path?: string;
  supports_reference_image: boolean;
  remark?: string;
  enabled: boolean;
  last_test_status: string;
  last_tested_at?: string;
  last_test_error?: string;
  created_at: string;
  updated_at: string;
};

export type ModelConfigUpdatePayload = Omit<ModelConfigPayload, "config_type" | "enabled" | "api_key"> & {
  api_key?: string;
  enabled?: boolean;
};

export type ProjectPayload = {
  title?: string;
  idea: string;
  target_platform?: string;
  genre?: string;
  episode_count: number;
  episode_duration: number;
  target_audience?: string;
  style?: string;
  remark?: string;
};

export type ProjectSummary = ProjectPayload & {
  id: string;
  title: string;
  total_duration: number;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ProjectWorldSnapshot = {
  id: string;
  project_id: string;
  source_world_book_id: string;
  source_version: number;
  name: string;
  genre: string;
  snapshot_content: string;
  entry_snapshot_content: string;
  loaded_at: string;
  updated_at: string;
};

export type ProjectWorldSnapshotPayload = {
  name: string;
  genre: string;
  snapshot_content: string;
  entry_snapshot_content: string;
};

export type ProjectArtifactStatus = "draft" | "confirmed" | "needs_review";

export type ProjectStoryOutlinePayload = {
  logline?: string;
  story_background?: string;
  core_conflict?: string;
  main_goal?: string;
  story_start?: string;
  plot_structure?: string;
  reversals?: string;
  emotion_curve?: string;
  foreshadowing?: string;
  character_arcs?: string;
  ending_direction?: string;
  pacing_advice?: string;
  capacity_advice?: string;
  notes?: string;
  status: ProjectArtifactStatus;
};

export type ProjectStoryOutline = ProjectStoryOutlinePayload & {
  id: string;
  project_id: string;
  created_at: string;
  updated_at: string;
};

export type StoryOutlineGeneratePayload = {
  user_requirements?: string;
  reference_draft_id?: string;
  write_mode?: "preview" | "apply";
};

export type StoryOutlineGenerationResult = {
  outline: ProjectStoryOutlinePayload;
  applied: boolean;
  saved_outline?: ProjectStoryOutline;
  context_summary: string;
};

export type StoryOutlineRewritePayload = {
  field: string;
  current_value: string;
  instruction: string;
  write_mode?: "preview" | "apply";
};

export type StoryOutlineRewriteResult = {
  field: string;
  value: string;
  applied: boolean;
  saved_outline?: ProjectStoryOutline;
};

export type StoryOutlineAssistMessage = {
  role: "user" | "assistant";
  content: string;
};

export type StoryOutlineAssistPatch = Partial<Omit<ProjectStoryOutlinePayload, "status">>;

export type StoryOutlineAssistPayload = {
  action: "start" | "reply";
  current_outline: ProjectStoryOutlinePayload;
  messages: StoryOutlineAssistMessage[];
  user_message?: string;
  client_request_id?: string;
};

export type StoryOutlineAssistCompletion = {
  required_fields: string[];
  completed_fields: string[];
  missing_fields: string[];
  is_complete: boolean;
};

export type StoryOutlineAssistResult = {
  assistant_message: string;
  outline_patch: StoryOutlineAssistPatch;
  completion: StoryOutlineAssistCompletion;
  field_notes: Record<string, string>;
  next_focus_fields: string[];
  request_id?: string;
  elapsed_ms?: number;
  stage_timings?: Record<string, number>;
};

export type ReferenceStoryStructureDraft = {
  id: string;
  project_id: string;
  source_type: "pasted" | "uploaded";
  source_filename?: string;
  source_text_excerpt?: string;
  story_type?: string;
  goal_model?: string;
  inciting_event_type?: string;
  conflict_model?: string;
  stage_structure?: string;
  reversal_mechanism?: string;
  emotion_curve?: string;
  foreshadowing_pattern?: string;
  ending_pattern?: string;
  adaptation_advice?: string;
  de_specificity_notes?: string;
  validation_status: "pending" | "passed" | "failed";
  validation_notes?: string;
  status: "draft" | "applied" | "discarded";
  outline_preview: ProjectStoryOutlinePayload;
  created_at: string;
  updated_at: string;
};

export type ReferenceStoryStructureExtractPayload = {
  source_type: "pasted" | "uploaded";
  source_filename?: string;
  source_text: string;
  user_requirements?: string;
};

export type ProjectEpisodeOutlinePayload = {
  title?: string;
  synopsis?: string;
  hook?: string;
  conflict?: string;
  reversal?: string;
  cliffhanger?: string;
  duration_minutes?: number;
  status: ProjectArtifactStatus;
};

export type ProjectEpisodeOutline = ProjectEpisodeOutlinePayload & {
  id: string;
  project_id: string;
  episode_no: number;
  created_at: string;
  updated_at: string;
};

export type ProjectEpisodeContentPayload = {
  title?: string;
  detailed_content?: string;
  chapter_summary?: string;
  hook?: string;
  key_beats?: string;
  previous_context_summary?: string;
  quality_check_notes?: string;
  status: ProjectArtifactStatus;
};

export type ProjectEpisodeContent = ProjectEpisodeContentPayload & {
  id: string;
  project_id: string;
  episode_no: number;
  word_count: number;
  created_at: string;
  updated_at: string;
};

export type EpisodeContentGenerationStatus = "candidate" | "adopted" | "discarded";

export type EpisodeContentGeneration = {
  id: string;
  project_id: string;
  episode_no: number;
  instruction?: string;
  input_snapshot: Record<string, unknown>;
  output_text: string;
  word_count: number;
  status: EpisodeContentGenerationStatus;
  client_request_id: string;
  model_config_id?: string;
  model_name?: string;
  elapsed_ms?: number;
  created_at: string;
  updated_at: string;
  adopted_at?: string;
};

export type EpisodeContentGenerationAdoptResult = {
  generation: EpisodeContentGeneration;
  content: ProjectEpisodeContent;
};

export type ScriptStatus = ProjectArtifactStatus | "pending_review";
export type ScriptBlockType = "action" | "dialogue" | "voiceover" | "transition";
export type ScriptTimeOfDay = "morning" | "day" | "dusk" | "night" | "other";
export type ScriptInteriorExterior = "interior" | "exterior" | "mixed";

export type ScriptCheckIssue = {
  code: string;
  severity: "error" | "warning" | "info";
  message: string;
  scene_id?: string;
  block_id?: string;
  details: Record<string, unknown>;
};

export type ScriptBlockPayload = {
  id?: string;
  block_type: ScriptBlockType;
  character_snapshot_id?: string;
  temporary_speaker_name?: string;
  content?: string;
  emotion?: string;
  performance_note?: string;
};

export type ScriptBlock = ScriptBlockPayload & {
  id: string;
  scene_id: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type ScriptScenePayload = {
  id?: string;
  title?: string;
  location?: string;
  time_of_day?: ScriptTimeOfDay;
  interior_exterior?: ScriptInteriorExterior;
  character_snapshot_ids: string[];
  manual_duration_seconds?: number;
  story_purpose?: string;
  blocks: ScriptBlockPayload[];
};

export type ScriptScene = Omit<ScriptScenePayload, "id" | "blocks"> & {
  id: string;
  script_id: string;
  scene_no: number;
  character_refs: Array<{ character_snapshot_id: string; name: string; updated_at: string }>;
  auto_duration_seconds: number;
  effective_duration_seconds: number;
  sort_order: number;
  blocks: ScriptBlock[];
  created_at: string;
  updated_at: string;
};

export type ProjectEpisodeScriptPayload = {
  revision: number | null;
  title?: string;
  manual_duration_seconds?: number;
  scenes: ScriptScenePayload[];
};

export type ProjectEpisodeScript = {
  id: string;
  project_id: string;
  episode_no: number;
  title?: string;
  revision: number;
  version: number;
  source_content_version?: string;
  auto_duration_seconds: number;
  manual_duration_seconds?: number;
  effective_duration_seconds: number;
  target_duration_seconds: number;
  duration_deviation_seconds: number;
  duration_deviation_percent: number;
  status: ScriptStatus;
  confirmed_at?: string;
  scenes: ScriptScene[];
  validation_issues: ScriptCheckIssue[];
  created_at: string;
  updated_at: string;
};

export type ScriptGenerationScope = "episode" | "scene" | "blocks";
export type ScriptRewritePreset = "more_satisfying" | "more_tragic" | "more_suspenseful" | "more_colloquial" | "short_video_pacing" | "compress_duration" | "stronger_cliffhanger";
export type ScriptGeneration = {
  id: string;
  project_id: string;
  episode_no: number;
  generation_scope: ScriptGenerationScope;
  target_scene_id?: string;
  target_block_ids: string[];
  rewrite_preset?: ScriptRewritePreset;
  instruction?: string;
  base_script_version?: number;
  base_script_revision?: number;
  input_snapshot: Record<string, unknown>;
  output_snapshot: Record<string, unknown>;
  status: "candidate" | "adopted" | "discarded";
  client_request_id: string;
  model_config_id?: string;
  model_name?: string;
  elapsed_ms?: number;
  adopted_at?: string;
  created_at: string;
  updated_at: string;
};

export type ScriptCheckResult = {
  id: string;
  script_id: string;
  script_version: number;
  script_revision: number;
  mode: "structure" | "full";
  semantic_check_status: "not_requested" | "succeeded" | "failed";
  issues: ScriptCheckIssue[];
  created_at: string;
};

export type ScriptVersionSummary = {
  version: number;
  source_content_version?: string;
  change_source: "manual_save" | "generation_adopt" | "migration";
  generation_id?: string;
  duration_seconds: number;
  scene_count: number;
  created_at: string;
};

export type ProjectStoryboardShotPayload = {
  shot_no: number;
  scene?: string;
  visual_prompt?: string;
  camera?: string;
  duration_seconds?: number;
  dialogue_or_voiceover?: string;
  status: ProjectArtifactStatus;
};

export type ProjectStoryboardShot = ProjectStoryboardShotPayload & {
  id: string;
  project_id: string;
  episode_no: number;
  created_at: string;
  updated_at: string;
};

export type ProjectCopywritingPayload = {
  subtitles?: string;
  platform_title?: string;
  platform_description?: string;
  publish_copy?: string;
  status: ProjectArtifactStatus;
};

export type ProjectCopywriting = ProjectCopywritingPayload & {
  id: string;
  project_id: string;
  episode_no: number;
  created_at: string;
  updated_at: string;
};

export type CharacterCardStatus = "draft" | "active" | "archived";
export type CharacterGender = "男" | "女";

export type CharacterCardPayload = {
  name: string;
  gender: CharacterGender;
  role_type: string;
  identity: string;
  background?: string;
  personality?: string;
  goal: string;
  motivation?: string;
  secret?: string;
  conflict_points?: string;
  relationship_notes?: string;
  speech_style?: string;
  catchphrases?: string;
  emotional_arc?: string;
  story_function?: string;
  visual_description?: string;
  image_keywords?: string;
  reference_image_url?: string;
  reference_local_path?: string;
  turnaround_prompt?: string;
  status: CharacterCardStatus;
};

export type CharacterCard = CharacterCardPayload & {
  id: string;
  version: number;
  turnaround_image_url?: string;
  turnaround_local_path?: string;
  turnaround_generation_prompt?: string;
  turnaround_status: "none" | "generated" | "confirmed" | "failed";
  turnaround_version: number;
  turnaround_confirmed_at?: string;
  created_at: string;
  updated_at: string;
};

export type CharacterImageAsset = {
  character_card_id: string;
  image_url: string;
  local_path: string;
  updated_at: string;
};

export type CharacterTurnaround = {
  character_card_id: string;
  image_url?: string;
  local_path?: string;
  generation_prompt?: string;
  status: "none" | "generated" | "confirmed" | "failed";
  version: number;
  confirmed_at?: string;
  updated_at: string;
};

export type ProjectCharacterSnapshot = {
  id: string;
  project_id: string;
  source_character_card_id: string;
  source_version: number;
  name: string;
  gender: CharacterGender;
  role_type: string;
  snapshot_content: string;
  visual_description?: string;
  reference_image_url?: string;
  reference_local_path?: string;
  loaded_at: string;
  updated_at: string;
};

export type ProjectCharacterSnapshotPayload = {
  name: string;
  gender: CharacterGender;
  role_type: string;
  snapshot_content: string;
  visual_description?: string;
  reference_image_url?: string;
  reference_local_path?: string;
};

export type WorldBookStatus = "draft" | "active" | "archived";
export type WorldEntryStatus = "active" | "disabled";
export type WorldEntryType =
  | "世界规则"
  | "地点"
  | "组织"
  | "阶层关系"
  | "历史事件"
  | "特殊物品"
  | "禁忌或限制"
  | "风格约束"
  | "其他";

export type WorldBookPayload = {
  name: string;
  genre: string;
  era_background?: string;
  world_rules: string;
  organizations?: string;
  locations?: string;
  social_structure?: string;
  taboo_or_constraints?: string;
  tone_style?: string;
  summary?: string;
  status: WorldBookStatus;
};

export type WorldBook = WorldBookPayload & {
  id: string;
  version: number;
  entry_count: number;
  active_entry_count: number;
  created_at: string;
  updated_at: string;
};

export type WorldEntryPayload = {
  title: string;
  entry_type: WorldEntryType;
  keywords?: string;
  content: string;
  applicable_scope?: string;
  priority: number;
  status: WorldEntryStatus;
};

export type WorldEntry = WorldEntryPayload & {
  id: string;
  world_book_id: string;
  created_at: string;
  updated_at: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {})
      }
    });
  } catch (err) {
    // 浏览器在后端未启动、端口不可达或 CORS 被拦截时通常只给出 Load failed/Failed to fetch。
    throw new Error(normalizeNetworkError(err));
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(normalizeHttpError(response.status, body?.detail));
  }

  return response.json() as Promise<T>;
}

function normalizeHttpError(status: number, detail: unknown) {
  if (typeof detail === "string" && detail !== "Not Found") {
    return detail;
  }
  if (detail && typeof detail === "object" && "message" in detail && typeof detail.message === "string") {
    return detail.message;
  }
  if (status === 404) {
    return "请求的接口或资源不存在，请确认后端服务已更新并已重启。";
  }
  return `Request failed: ${status}`;
}

function normalizeNetworkError(err: unknown) {
  const rawMessage = err instanceof Error ? err.message : "";
  if (rawMessage === "Load failed" || rawMessage === "Failed to fetch" || rawMessage.includes("NetworkError")) {
    return `无法连接后端服务，请确认 API 服务已启动并可访问：${API_BASE_URL}`;
  }
  return rawMessage || "请求后端服务失败，请稍后重试。";
}

export function listModelConfigs(configType?: "text" | "image") {
  const query = configType ? `?config_type=${configType}` : "";
  return request<ModelConfig[]>(`/api/model-configs${query}`);
}

export function getModelConfig(configId: string) {
  return request<ModelConfig>(`/api/model-configs/${configId}`);
}

export function createModelConfig(payload: ModelConfigPayload) {
  return request<ModelConfig>("/api/model-configs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateModelConfig(configId: string, payload: ModelConfigUpdatePayload) {
  return request<ModelConfig>(`/api/model-configs/${configId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function deleteModelConfig(configId: string) {
  return request<{ ok: boolean }>(`/api/model-configs/${configId}`, {
    method: "DELETE"
  });
}

export function enableModelConfig(configId: string) {
  return request<ModelConfig>(`/api/model-configs/${configId}/enable`, {
    method: "POST"
  });
}

export function testModelConfig(configId: string) {
  return request(`/api/model-configs/${configId}/test`, {
    method: "POST"
  });
}

export function createProject(payload: ProjectPayload) {
  return request<ProjectSummary>("/api/projects", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listProjects() {
  return request<ProjectSummary[]>("/api/projects");
}

export function getProject(projectId: string) {
  return request<ProjectSummary>(`/api/projects/${projectId}`);
}

export function updateProject(projectId: string, payload: ProjectPayload) {
  return request<ProjectSummary>(`/api/projects/${projectId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function listProjectWorldSnapshots(projectId: string) {
  return request<ProjectWorldSnapshot[]>(`/api/projects/${projectId}/world-snapshots`);
}

export function deleteProjectWorldSnapshot(projectId: string, snapshotId: string) {
  return request<{ ok: boolean }>(`/api/projects/${projectId}/world-snapshots/${snapshotId}`, {
    method: "DELETE"
  });
}

export function updateProjectWorldSnapshot(projectId: string, snapshotId: string, payload: ProjectWorldSnapshotPayload) {
  return request<ProjectWorldSnapshot>(`/api/projects/${projectId}/world-snapshots/${snapshotId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function listProjectCharacterSnapshots(projectId: string) {
  return request<ProjectCharacterSnapshot[]>(`/api/projects/${projectId}/character-snapshots`);
}

export function deleteProjectCharacterSnapshot(projectId: string, snapshotId: string) {
  return request<{ ok: boolean }>(`/api/projects/${projectId}/character-snapshots/${snapshotId}`, {
    method: "DELETE"
  });
}

export function updateProjectCharacterSnapshot(projectId: string, snapshotId: string, payload: ProjectCharacterSnapshotPayload) {
  return request<ProjectCharacterSnapshot>(`/api/projects/${projectId}/character-snapshots/${snapshotId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function getProjectStoryOutline(projectId: string) {
  return request<ProjectStoryOutline | null>(`/api/projects/${projectId}/story-outline`);
}

export function updateProjectStoryOutline(projectId: string, payload: ProjectStoryOutlinePayload) {
  return request<ProjectStoryOutline>(`/api/projects/${projectId}/story-outline`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function generateProjectStoryOutline(projectId: string, payload: StoryOutlineGeneratePayload) {
  return request<StoryOutlineGenerationResult>(`/api/projects/${projectId}/story-outline/generate`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function rewriteProjectStoryOutlineField(projectId: string, payload: StoryOutlineRewritePayload) {
  return request<StoryOutlineRewriteResult>(`/api/projects/${projectId}/story-outline/rewrite`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function assistProjectStoryOutline(projectId: string, payload: StoryOutlineAssistPayload) {
  return request<StoryOutlineAssistResult>(`/api/projects/${projectId}/story-outline/assist`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function extractReferenceStoryStructure(projectId: string, payload: ReferenceStoryStructureExtractPayload) {
  return request<ReferenceStoryStructureDraft>(`/api/projects/${projectId}/story-structure-drafts/extract`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listReferenceStoryStructureDrafts(projectId: string) {
  return request<ReferenceStoryStructureDraft[]>(`/api/projects/${projectId}/story-structure-drafts`);
}

export function applyReferenceStoryStructureDraft(projectId: string, draftId: string, applyMode: "fill_empty" | "overwrite") {
  return request<ProjectStoryOutline>(`/api/projects/${projectId}/story-structure-drafts/${draftId}/apply`, {
    method: "POST",
    body: JSON.stringify({ apply_mode: applyMode })
  });
}

export function discardReferenceStoryStructureDraft(projectId: string, draftId: string) {
  return request<ReferenceStoryStructureDraft>(`/api/projects/${projectId}/story-structure-drafts/${draftId}/discard`, {
    method: "POST"
  });
}

export function listProjectEpisodeOutlines(projectId: string) {
  return request<ProjectEpisodeOutline[]>(`/api/projects/${projectId}/episode-outlines`);
}

export function updateProjectEpisodeOutline(projectId: string, episodeNo: number, payload: ProjectEpisodeOutlinePayload) {
  return request<ProjectEpisodeOutline>(`/api/projects/${projectId}/episode-outlines/${episodeNo}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function getProjectEpisodeContent(projectId: string, episodeNo: number) {
  return request<ProjectEpisodeContent | null>(`/api/projects/${projectId}/episode-contents/${episodeNo}`);
}

export function updateProjectEpisodeContent(projectId: string, episodeNo: number, payload: ProjectEpisodeContentPayload) {
  return request<ProjectEpisodeContent>(`/api/projects/${projectId}/episode-contents/${episodeNo}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function generateProjectEpisodeContent(
  projectId: string,
  episodeNo: number,
  payload: { instruction?: string; client_request_id: string }
) {
  return request<EpisodeContentGeneration>(`/api/projects/${projectId}/episode-contents/${episodeNo}/generations`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listProjectEpisodeContentGenerations(projectId: string, episodeNo: number) {
  return request<EpisodeContentGeneration[]>(`/api/projects/${projectId}/episode-contents/${episodeNo}/generations`);
}

export function updateProjectEpisodeContentGeneration(
  projectId: string,
  episodeNo: number,
  generationId: string,
  outputText: string
) {
  return request<EpisodeContentGeneration>(
    `/api/projects/${projectId}/episode-contents/${episodeNo}/generations/${generationId}`,
    { method: "PUT", body: JSON.stringify({ output_text: outputText }) }
  );
}

export function adoptProjectEpisodeContentGeneration(
  projectId: string,
  episodeNo: number,
  generationId: string
) {
  return request<EpisodeContentGenerationAdoptResult>(
    `/api/projects/${projectId}/episode-contents/${episodeNo}/generations/${generationId}/adopt`,
    { method: "POST" }
  );
}

export function discardProjectEpisodeContentGeneration(
  projectId: string,
  episodeNo: number,
  generationId: string
) {
  return request<EpisodeContentGeneration>(
    `/api/projects/${projectId}/episode-contents/${episodeNo}/generations/${generationId}/discard`,
    { method: "POST" }
  );
}

export function getProjectEpisodeScript(projectId: string, episodeNo: number) {
  return request<ProjectEpisodeScript | null>(`/api/projects/${projectId}/episode-scripts/${episodeNo}`);
}

export function updateProjectEpisodeScript(projectId: string, episodeNo: number, payload: ProjectEpisodeScriptPayload) {
  return request<ProjectEpisodeScript>(`/api/projects/${projectId}/episode-scripts/${episodeNo}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function listProjectScriptGenerations(projectId: string, episodeNo: number) {
  return request<ScriptGeneration[]>(`/api/projects/${projectId}/episode-scripts/${episodeNo}/generations`);
}

export function createProjectScriptGeneration(
  projectId: string,
  episodeNo: number,
  payload: {
    generation_scope: ScriptGenerationScope;
    target_scene_id?: string;
    target_block_ids: string[];
    rewrite_preset?: ScriptRewritePreset;
    instruction?: string;
    client_request_id: string;
    base_script_version: number | null;
    base_script_revision: number | null;
  }
) {
  return request<ScriptGeneration>(`/api/projects/${projectId}/episode-scripts/${episodeNo}/generations`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function adoptProjectScriptGeneration(projectId: string, episodeNo: number, generationId: string, revision: number | null) {
  return request<{ generation: ScriptGeneration; script: ProjectEpisodeScript }>(
    `/api/projects/${projectId}/episode-scripts/${episodeNo}/generations/${generationId}/adopt`,
    { method: "POST", body: JSON.stringify({ revision }) }
  );
}

export function discardProjectScriptGeneration(projectId: string, episodeNo: number, generationId: string) {
  return request<ScriptGeneration>(`/api/projects/${projectId}/episode-scripts/${episodeNo}/generations/${generationId}/discard`, {
    method: "POST"
  });
}

export function checkProjectEpisodeScript(projectId: string, episodeNo: number, revision: number, mode: "structure" | "full" = "full") {
  return request<ScriptCheckResult>(`/api/projects/${projectId}/episode-scripts/${episodeNo}/checks`, {
    method: "POST",
    body: JSON.stringify({ revision, mode })
  });
}

export function submitProjectEpisodeScript(projectId: string, episodeNo: number, revision: number) {
  return request<ProjectEpisodeScript>(`/api/projects/${projectId}/episode-scripts/${episodeNo}/submit-review`, {
    method: "POST",
    body: JSON.stringify({ revision })
  });
}

export function confirmProjectEpisodeScript(projectId: string, episodeNo: number, revision: number) {
  return request<ProjectEpisodeScript>(`/api/projects/${projectId}/episode-scripts/${episodeNo}/confirm`, {
    method: "POST",
    body: JSON.stringify({ revision })
  });
}

export function listProjectEpisodeScriptVersions(projectId: string, episodeNo: number) {
  return request<ScriptVersionSummary[]>(`/api/projects/${projectId}/episode-scripts/${episodeNo}/versions`);
}

export function getProjectEpisodeScriptVersion(projectId: string, episodeNo: number, version: number) {
  return request<ProjectEpisodeScript>(`/api/projects/${projectId}/episode-scripts/${episodeNo}/versions/${version}`);
}

export function listProjectStoryboardShots(projectId: string, episodeNo: number) {
  return request<ProjectStoryboardShot[]>(`/api/projects/${projectId}/storyboard-shots/${episodeNo}`);
}

export function createProjectStoryboardShot(projectId: string, episodeNo: number, payload: ProjectStoryboardShotPayload) {
  return request<ProjectStoryboardShot>(`/api/projects/${projectId}/storyboard-shots/${episodeNo}`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateProjectStoryboardShot(
  projectId: string,
  episodeNo: number,
  shotId: string,
  payload: ProjectStoryboardShotPayload
) {
  return request<ProjectStoryboardShot>(`/api/projects/${projectId}/storyboard-shots/${episodeNo}/${shotId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function deleteProjectStoryboardShot(projectId: string, episodeNo: number, shotId: string) {
  return request<{ ok: boolean }>(`/api/projects/${projectId}/storyboard-shots/${episodeNo}/${shotId}`, {
    method: "DELETE"
  });
}

export function getProjectCopywriting(projectId: string, episodeNo: number) {
  return request<ProjectCopywriting | null>(`/api/projects/${projectId}/copywriting/${episodeNo}`);
}

export function updateProjectCopywriting(projectId: string, episodeNo: number, payload: ProjectCopywritingPayload) {
  return request<ProjectCopywriting>(`/api/projects/${projectId}/copywriting/${episodeNo}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function listCharacterCards(filters: { search?: string; gender?: CharacterGender; role_type?: string; status?: string } = {}) {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.gender) params.set("gender", filters.gender);
  if (filters.role_type) params.set("role_type", filters.role_type);
  if (filters.status) params.set("status", filters.status);
  const query = params.toString();
  return request<CharacterCard[]>(`/api/character-cards${query ? `?${query}` : ""}`);
}

export function createCharacterCard(payload: CharacterCardPayload) {
  return request<CharacterCard>("/api/character-cards", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getCharacterCard(cardId: string) {
  return request<CharacterCard>(`/api/character-cards/${cardId}`);
}

export function updateCharacterCard(cardId: string, payload: CharacterCardPayload) {
  return request<CharacterCard>(`/api/character-cards/${cardId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function archiveCharacterCard(cardId: string) {
  return request<CharacterCard>(`/api/character-cards/${cardId}/archive`, {
    method: "POST"
  });
}

export function activateCharacterCard(cardId: string) {
  return request<CharacterCard>(`/api/character-cards/${cardId}/activate`, {
    method: "POST"
  });
}

export function loadCharacterCardToProject(projectId: string, sourceCharacterCardId: string) {
  return request(`/api/projects/${projectId}/character-snapshots`, {
    method: "POST",
    body: JSON.stringify({
      source_character_card_id: sourceCharacterCardId,
      load_mode: "new"
    })
  });
}

export function uploadCharacterReferenceImage(
  cardId: string,
  payload: { filename: string; content_type: string; data_url: string }
) {
  return request<CharacterImageAsset>(`/api/character-cards/${cardId}/reference-images`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function generateCharacterTurnaround(cardId: string, prompt?: string) {
  return request<CharacterTurnaround>(`/api/character-cards/${cardId}/turnaround-images`, {
    method: "POST",
    body: JSON.stringify({ prompt: prompt || undefined })
  });
}

export function confirmCharacterTurnaround(cardId: string) {
  return request<CharacterTurnaround>(`/api/character-cards/${cardId}/turnaround-images/confirm`, {
    method: "POST"
  });
}

export function confirmCharacterTurnaroundByVersion(cardId: string, version: number) {
  return request<CharacterTurnaround>(`/api/character-cards/${cardId}/turnaround-images/${version}/confirm`, {
    method: "POST"
  });
}

export function listWorldBooks(filters: { search?: string; genre?: string; status?: string } = {}) {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.genre) params.set("genre", filters.genre);
  if (filters.status) params.set("status", filters.status);
  const query = params.toString();
  return request<WorldBook[]>(`/api/world-books${query ? `?${query}` : ""}`);
}

export function createWorldBook(payload: WorldBookPayload) {
  return request<WorldBook>("/api/world-books", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getWorldBook(worldBookId: string) {
  return request<WorldBook>(`/api/world-books/${worldBookId}`);
}

export function updateWorldBook(worldBookId: string, payload: WorldBookPayload) {
  return request<WorldBook>(`/api/world-books/${worldBookId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function archiveWorldBook(worldBookId: string) {
  return request<WorldBook>(`/api/world-books/${worldBookId}/archive`, {
    method: "POST"
  });
}

export function activateWorldBook(worldBookId: string) {
  return request<WorldBook>(`/api/world-books/${worldBookId}/activate`, {
    method: "POST"
  });
}

export function listWorldEntries(worldBookId: string) {
  return request<WorldEntry[]>(`/api/world-books/${worldBookId}/entries`);
}

export function createWorldEntry(worldBookId: string, payload: WorldEntryPayload) {
  return request<WorldEntry>(`/api/world-books/${worldBookId}/entries`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateWorldEntry(worldBookId: string, entryId: string, payload: WorldEntryPayload) {
  return request<WorldEntry>(`/api/world-books/${worldBookId}/entries/${entryId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function disableWorldEntry(worldBookId: string, entryId: string) {
  return request<WorldEntry>(`/api/world-books/${worldBookId}/entries/${entryId}/disable`, {
    method: "POST"
  });
}

export function enableWorldEntry(worldBookId: string, entryId: string) {
  return request<WorldEntry>(`/api/world-books/${worldBookId}/entries/${entryId}/enable`, {
    method: "POST"
  });
}

export function loadWorldBookToProject(projectId: string, sourceWorldBookId: string) {
  return request(`/api/projects/${projectId}/world-snapshots`, {
    method: "POST",
    body: JSON.stringify({
      source_world_book_id: sourceWorldBookId,
      load_mode: "new"
    })
  });
}

export function resolveAssetUrl(url?: string) {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("data:")) {
    return url;
  }
  return `${API_BASE_URL}${url}`;
}
