"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, Check, ChevronDown, ChevronRight, Copy, ExternalLink, List, Maximize2, Menu, Play, Plus, RefreshCw, Save, Trash2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SimpleSelect } from "@/components/ui/simple-select";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle
} from "@/components/ui/alert-dialog";
import {
  adoptShotVideoGeneration, cancelShotVideoGeneration,
  createProjectStoryboardShot, deleteProjectStoryboardShot, duplicateProjectStoryboardShot,
  createShotVideoGeneration,
  generateProjectStoryboardScene, getProjectStoryboard, reassignProjectStoryboardShot,
  listModelConfigs, listShotVideoGenerations, refreshShotVideoGeneration,
  reorderProjectStoryboardScene, resolveAssetUrl, updateProjectStoryboardShot
} from "@/lib/api";
import type {
  ModelConfig,
  ProjectCharacterSnapshot,
  ProjectStoryboard,
  ProjectStoryboardShot,
  ProjectStoryboardShotPayload,
  ShotVideoGeneration,
  ShotVideoGenerationCreatePayload,
  StoryboardSceneGroup
} from "@/lib/api";
import type { ProjectWorkbenchState } from "../_hooks/useProjectWorkbench";
import type { Stage } from "../_utils/workbenchTypes";
import { EpisodePicker } from "./shared";

type SwitchTarget = { kind: "shot"; id: string } | { kind: "episode"; episodeNo: number } | { kind: "stage"; stage: Stage };
type ShotStatus = ProjectStoryboardShot["status"];
type VideoGenerationOptions = { resolution: string; aspect_ratio: string; duration_seconds: string; use_reference_images: boolean };

const defaultVideoGenerationOptions: VideoGenerationOptions = { resolution: "", aspect_ratio: "", duration_seconds: "", use_reference_images: false };

const videoResolutionOptions = [
  { label: "默认 720p", value: "" },
  { label: "720p", value: "720p" },
  { label: "1080p", value: "1080p" }
];

const videoAspectRatioOptions = [
  { label: "默认（提示词画幅或 16:9）", value: "" },
  { label: "16:9 横屏", value: "16:9" },
  { label: "9:16 竖屏", value: "9:16" },
  { label: "1:1 方形", value: "1:1" },
  { label: "4:3 横屏", value: "4:3" },
  { label: "3:4 竖屏", value: "3:4" },
  { label: "21:9 宽银幕", value: "21:9" }
];

const customPresetValue = "__custom__";

const shotSizeOptions = [
  { label: "未设置", value: "" },
  { label: "大远景", value: "大远景" },
  { label: "远景", value: "远景" },
  { label: "全景", value: "全景" },
  { label: "中全景", value: "中全景" },
  { label: "中景", value: "中景" },
  { label: "中近景", value: "中近景" },
  { label: "近景", value: "近景" },
  { label: "特写", value: "特写" },
  { label: "大特写", value: "大特写" },
  { label: "插入镜头", value: "插入镜头" },
  { label: "过肩镜头", value: "过肩镜头" },
  { label: "双人镜头", value: "双人镜头" },
  { label: "群像镜头", value: "群像镜头" },
];

const cameraAngleOptions = [
  { label: "未设置", value: "" },
  { label: "平视", value: "平视" },
  { label: "低角度仰拍", value: "低角度仰拍" },
  { label: "高角度俯拍", value: "高角度俯拍" },
  { label: "鸟瞰 / 顶拍", value: "鸟瞰 / 顶拍" },
  { label: "虫视角", value: "虫视角" },
  { label: "主观视角 POV", value: "主观视角 POV" },
  { label: "过肩视角", value: "过肩视角" },
  { label: "侧面机位", value: "侧面机位" },
  { label: "背面跟拍", value: "背面跟拍" },
  { label: "正反打", value: "正反打" },
  { label: "倾斜构图 / 荷兰角", value: "倾斜构图 / 荷兰角" },
  { label: "镜中视角", value: "镜中视角" },
  { label: "监控视角", value: "监控视角" },
  { label: "手机屏幕视角", value: "手机屏幕视角" },
];

const cameraMovementOptions = [
  { label: "未设置", value: "" },
  { label: "固定机位", value: "固定机位" },
  { label: "缓慢推进", value: "缓慢推进" },
  { label: "快速推进", value: "快速推进" },
  { label: "缓慢拉远", value: "缓慢拉远" },
  { label: "横向摇镜", value: "横向摇镜" },
  { label: "上下摇镜", value: "上下摇镜" },
  { label: "横移跟拍", value: "横移跟拍" },
  { label: "前后跟拍", value: "前后跟拍" },
  { label: "环绕运镜", value: "环绕运镜" },
  { label: "手持晃动", value: "手持晃动" },
  { label: "稳定器跟随", value: "稳定器跟随" },
  { label: "升降机位", value: "升降机位" },
  { label: "变焦推进", value: "变焦推进" },
  { label: "甩镜转场", value: "甩镜转场" },
  { label: "快速摇移", value: "快速摇移" },
  { label: "延时 / 慢动作运动", value: "延时 / 慢动作运动" },
];

const compositionOptions = [
  { label: "未设置", value: "" },
  { label: "人物居中", value: "人物居中" },
  { label: "三分法构图", value: "三分法构图" },
  { label: "对称构图", value: "对称构图" },
  { label: "前景遮挡", value: "前景遮挡" },
  { label: "框架式构图", value: "框架式构图" },
  { label: "引导线构图", value: "引导线构图" },
  { label: "浅景深突出主体", value: "浅景深突出主体" },
  { label: "留白构图", value: "留白构图" },
  { label: "压迫式近距离构图", value: "压迫式近距离构图" },
  { label: "主体偏一侧", value: "主体偏一侧" },
  { label: "多人层次站位", value: "多人层次站位" },
  { label: "门框 / 窗框分割画面", value: "门框 / 窗框分割画面" },
];

const expressionOptions = [
  { label: "未设置", value: "" },
  { label: "平静", value: "平静" },
  { label: "警觉", value: "警觉" },
  { label: "惊讶", value: "惊讶" },
  { label: "恐惧", value: "恐惧" },
  { label: "愤怒", value: "愤怒" },
  { label: "压抑克制", value: "压抑克制" },
  { label: "悲伤", value: "悲伤" },
  { label: "含泪", value: "含泪" },
  { label: "冷笑", value: "冷笑" },
  { label: "怀疑", value: "怀疑" },
  { label: "坚定", value: "坚定" },
  { label: "崩溃", value: "崩溃" },
  { label: "恍然大悟", value: "恍然大悟" },
];

const negativePromptPresets = [
  {
    label: "画质瑕疵",
    text: "低清晰度，模糊，噪点，过曝，欠曝，压缩伪影"
  },
  {
    label: "人物变形",
    text: "畸形五官，面部崩坏，多余手指，手部变形，肢体扭曲，人物身份变化"
  },
  {
    label: "文字水印",
    text: "字幕，文字，Logo，水印，时间码，界面元素"
  },
  {
    label: "运动异常",
    text: "画面闪烁，镜头抖动，跳帧，运动拖影，主体漂移"
  },
  {
    label: "风格偏差",
    text: "卡通化，油画感，过度美颜，塑料皮肤，非写实光影"
  },
];

const statusLabels: Record<ShotStatus, string> = {
  draft: "草稿", pending_review: "待审核", confirmed: "已确认", needs_review: "需检查"
};

const sourceStatusLabels: Record<string, string> = {
  draft: "草稿", pending_review: "待审核", confirmed: "已确认", needs_review: "需检查"
};

function payloadFromShot(shot: ProjectStoryboardShot): ProjectStoryboardShotPayload {
  const prompt = shot.prompt ?? {};
  return {
    revision: shot.revision,
    source_scene_id: shot.source_scene_id,
    shot_size: shot.shot_size,
    subject_description: shot.subject_description,
    visual_description: shot.visual_description,
    action: shot.action,
    duration_seconds: shot.duration_seconds,
    camera_angle: shot.camera_angle,
    camera_movement: shot.camera_movement,
    composition: shot.composition,
    character_snapshot_ids: shot.character_snapshot_ids ?? [],
    expression: shot.expression,
    environment: shot.environment,
    props: shot.props ?? [],
    source_block_ids: shot.source_block_ids ?? [],
    dialogue_snapshot: shot.dialogue_snapshot,
    voiceover_snapshot: shot.voiceover_snapshot,
    sound_effect: shot.sound_effect,
    music_note: shot.music_note,
    continuity_note: shot.continuity_note,
    status: shot.status,
    prompt: {
      ...prompt,
      image_prompt: undefined,
      video_prompt: prompt.video_prompt || prompt.seedance_prompt,
      seedance_prompt: undefined,
      reference_asset_ids: prompt.reference_asset_ids ?? []
    }
  };
}

function emptyPayload(sceneId?: string): ProjectStoryboardShotPayload {
  return {
    source_scene_id: sceneId,
    shot_size: "中景",
    duration_seconds: 3,
    character_snapshot_ids: [], props: [], source_block_ids: [], status: "draft",
    prompt: { reference_asset_ids: [] }
  };
}

function cleanPayload(payload: ProjectStoryboardShotPayload): ProjectStoryboardShotPayload {
  const clean = (value?: string) => value?.trim() || undefined;
  return {
    ...payload,
    shot_size: clean(payload.shot_size), subject_description: clean(payload.subject_description),
    visual_description: clean(payload.visual_description), action: clean(payload.action),
    camera_angle: clean(payload.camera_angle), camera_movement: clean(payload.camera_movement),
    composition: clean(payload.composition), expression: clean(payload.expression),
    environment: clean(payload.environment), dialogue_snapshot: clean(payload.dialogue_snapshot),
    voiceover_snapshot: clean(payload.voiceover_snapshot), sound_effect: clean(payload.sound_effect),
    music_note: clean(payload.music_note), continuity_note: clean(payload.continuity_note),
    character_snapshot_ids: payload.character_snapshot_ids ?? [], props: payload.props ?? [],
    source_block_ids: payload.source_block_ids ?? [],
    prompt: {
      ...payload.prompt,
      image_prompt: undefined, video_prompt: clean(payload.prompt?.video_prompt),
      negative_prompt: clean(payload.prompt?.negative_prompt), seedance_prompt: undefined,
      first_frame_description: clean(payload.prompt?.first_frame_description),
      last_frame_description: clean(payload.prompt?.last_frame_description),
      aspect_ratio: clean(payload.prompt?.aspect_ratio),
      reference_asset_ids: payload.prompt?.reference_asset_ids ?? []
    }
  };
}

function videoCreatePayload(options: VideoGenerationOptions): ShotVideoGenerationCreatePayload | undefined {
  const payload: ShotVideoGenerationCreatePayload = {};
  if (options.resolution) payload.resolution = options.resolution;
  if (options.aspect_ratio) payload.aspect_ratio = options.aspect_ratio;
  const duration = Number(options.duration_seconds);
  if (Number.isFinite(duration) && duration > 0) payload.duration_seconds = duration;
  if (options.use_reference_images) payload.use_reference_images = true;
  return Object.keys(payload).length ? payload : undefined;
}

function cleanText(value?: string | null) {
  return value?.trim() ?? "";
}

function snapshotContent(snapshot: ProjectCharacterSnapshot): Record<string, unknown> {
  try {
    const data = JSON.parse(snapshot.snapshot_content || "{}");
    return data && typeof data === "object" && !Array.isArray(data) ? data as Record<string, unknown> : {};
  } catch {
    return {};
  }
}

function snapshotContentText(snapshot: ProjectCharacterSnapshot, field: string) {
  const value = snapshotContent(snapshot)[field];
  return typeof value === "string" ? value.trim() : "";
}

function isPublicReferenceUrl(value?: string | null) {
  const url = cleanText(value);
  if (!/^https?:\/\//i.test(url)) return false;
  try {
    const hostname = new URL(url).hostname.toLowerCase();
    if (hostname === "localhost" || hostname.endsWith(".local")) return false;
    if (/^(127\.|10\.|192\.168\.|169\.254\.)/.test(hostname)) return false;
    if (/^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname)) return false;
    if (hostname === "::1") return false;
    return true;
  } catch {
    return false;
  }
}

function characterReferenceImageUrl(snapshot: ProjectCharacterSnapshot) {
  const candidates = [
    snapshotContentText(snapshot, "turnaround_image_url"),
    snapshot.reference_image_url,
    snapshotContentText(snapshot, "reference_image_url"),
  ];
  return candidates.find((url) => isPublicReferenceUrl(url)) ?? "";
}

function previewLine(label: string, value?: string | null) {
  const text = cleanText(value);
  return text ? `${label}：${text}` : "";
}

function buildVideoPromptPreview(draft: ProjectStoryboardShotPayload, characterSnapshots: ProjectCharacterSnapshot[]) {
  const supplementText = cleanText(draft.prompt?.video_prompt) || cleanText(draft.prompt?.seedance_prompt);
  const promptSource = supplementText ? "高级补充" : "分镜字段";
  const snapshotById = new Map(characterSnapshots.map((snapshot) => [snapshot.id, snapshot]));
  const shotCharacters = (draft.character_snapshot_ids ?? []).map((id) => snapshotById.get(id)).filter(Boolean) as ProjectCharacterSnapshot[];
  const missingCharacterIds = (draft.character_snapshot_ids ?? []).filter((id) => !snapshotById.has(id));
  const isMainCharacter = (snapshot: ProjectCharacterSnapshot) => /主角|男主|女主|protagonist/i.test(snapshot.role_type);
  const mainCharacters = shotCharacters.filter(isMainCharacter);
  const charactersToCheck = mainCharacters.length ? mainCharacters : shotCharacters;
  const characterLines = shotCharacters.map((snapshot) => {
    const identity = [snapshot.gender, snapshot.role_type].filter(Boolean).join("，");
    const prefix = identity ? `${snapshot.name}（${identity}）` : snapshot.name;
    const visual = cleanText(snapshot.visual_description);
    return visual ? `${prefix}：${visual}` : prefix;
  });
  const visualLines = [
    previewLine("主体", draft.subject_description),
    previewLine("核心画面", draft.visual_description),
    previewLine("动作", draft.action),
    previewLine("景别", draft.shot_size),
    previewLine("机位/角度", draft.camera_angle),
    previewLine("运镜", draft.camera_movement),
    previewLine("构图", draft.composition),
    previewLine("表情", draft.expression),
    previewLine("环境", draft.environment),
    (draft.props ?? []).length ? `道具：${(draft.props ?? []).join("、")}` : "",
  ].filter(Boolean);
  const sourceLines = [
    draft.subject_description,
    draft.visual_description,
    draft.action,
    draft.environment,
    (draft.props ?? []).join("、"),
  ].map((item) => cleanText(item)).filter(Boolean);
  const frameLines = [
    previewLine("首帧", draft.prompt?.first_frame_description),
    previewLine("尾帧", draft.prompt?.last_frame_description),
  ].filter(Boolean);
  const missingVisualCharacters = charactersToCheck.filter((snapshot) => !cleanText(snapshot.visual_description));
  const missingReferenceCharacters = charactersToCheck.filter((snapshot) => !cleanText(snapshot.reference_image_url) && !snapshotContentText(snapshot, "turnaround_image_url") && !cleanText(snapshot.reference_local_path));
  const referenceCount = shotCharacters.filter((snapshot) => cleanText(snapshot.reference_image_url) || snapshotContentText(snapshot, "turnaround_image_url") || cleanText(snapshot.reference_local_path)).length;
  const sendableReferenceCharacters = shotCharacters.filter((snapshot) => characterReferenceImageUrl(snapshot));
  const finalSections = [
    visualLines.length ? `镜头视觉：\n${visualLines.map((line) => `- ${line}`).join("\n")}` : "",
    characterLines.length ? `角色一致性：\n${characterLines.map((line) => `- ${line}`).join("\n")}` : "",
    supplementText ? `生成补充：\n- ${supplementText}` : "",
    frameLines.length ? `首尾帧约束：\n${frameLines.map((line) => `- ${line}`).join("\n")}` : "",
    cleanText(draft.prompt?.negative_prompt) ? `负面提示：${cleanText(draft.prompt?.negative_prompt)}` : "",
  ].filter(Boolean);

  return {
    promptSource,
    supplementText,
    shotCharacters,
    characterLines,
    visualLines,
    frameLines,
    finalText: finalSections.join("\n"),
    hasGenerationSource: Boolean(supplementText || sourceLines.length),
    referenceCount,
    sendableReferenceCharacters,
    missingCharacterIds,
    missingVisualCharacters,
    missingReferenceCharacters,
  };
}

function CharacterAppearancePicker({
  selectedIds,
  candidates,
  unassigned,
  onChange,
}: {
  selectedIds: string[];
  candidates: ProjectCharacterSnapshot[];
  unassigned: boolean;
  onChange: (ids: string[]) => void;
}) {
  const selectedSet = new Set(selectedIds);
  const toggle = (id: string, checked: boolean) => {
    onChange(checked ? [...selectedIds, id] : selectedIds.filter((item) => item !== id));
  };
  const selectedCount = candidates.filter((character) => selectedSet.has(character.id)).length;
  return <section className="md:col-span-2 rounded-lg border bg-background p-4">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 className="text-sm font-semibold">{unassigned ? "出镜人物（未归属场次）" : "出镜人物"}</h3>
        <p className="mt-1 text-xs text-muted-foreground">
          {unassigned ? "当前镜头未归属场次，可从项目角色中选择；建议先归属场次以收紧人物范围。" : "候选来自来源剧本场次；被选人物会进入视频生成的人物锚点和参考图统计。"}
        </p>
      </div>
      <Badge variant={selectedCount ? "secondary" : "outline"}>{selectedCount}/{candidates.length}</Badge>
    </div>
    <div className="mt-3 grid gap-2 md:grid-cols-2">
      {candidates.map((character) => {
        const hasVisual = Boolean(cleanText(character.visual_description));
        const hasSendableReference = Boolean(characterReferenceImageUrl(character));
        return <label key={character.id} className="flex min-w-0 items-start gap-3 rounded-md border bg-muted/20 p-3 text-sm">
          <Checkbox className="mt-0.5" checked={selectedSet.has(character.id)} onCheckedChange={(checked) => toggle(character.id, checked === true)} />
          <span className="min-w-0 flex-1">
            <span className="flex flex-wrap items-center gap-2">
              <span className="font-medium">{character.name}</span>
              {character.role_type ? <Badge variant="outline">{character.role_type}</Badge> : null}
            </span>
            <span className="mt-2 flex flex-wrap gap-1.5">
              <Badge variant={hasVisual ? "secondary" : "outline"}>{hasVisual ? "有视觉描述" : "缺视觉描述"}</Badge>
              <Badge variant={hasSendableReference ? "secondary" : "outline"}>{hasSendableReference ? "可发送参考图" : "无公网参考图"}</Badge>
            </span>
          </span>
        </label>;
      })}
    </div>
    {!candidates.length ? <p className="mt-3 rounded-md bg-muted/50 p-3 text-sm text-muted-foreground">暂无可选项目角色。请先在项目资料中加载角色。</p> : null}
    {selectedIds.length === 0 ? <p className="mt-3 text-xs text-muted-foreground">未选择出镜人物时仍可生成视频，但不会注入人物一致性锚点，也无法发送角色参考图。</p> : null}
  </section>;
}

export function StoryboardWorkbench({ workbench }: { workbench: ProjectWorkbenchState }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [storyboard, setStoryboard] = useState<ProjectStoryboard | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [draft, setDraft] = useState<ProjectStoryboardShotPayload | null>(null);
  const [savedDraft, setSavedDraft] = useState("");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | ShotStatus>("all");
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [pendingSwitch, setPendingSwitch] = useState<SwitchTarget | null>(null);
  const [navOpen, setNavOpen] = useState(false);
  const [generationStates, setGenerationStates] = useState<Record<string, "running" | "succeeded" | "failed">>({});
  const [videoGenerations, setVideoGenerations] = useState<ShotVideoGeneration[]>([]);
  const [videoConfigs, setVideoConfigs] = useState<ModelConfig[]>([]);
  const [videoBusy, setVideoBusy] = useState(false);
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoOptions, setVideoOptions] = useState<VideoGenerationOptions>(defaultVideoGenerationOptions);

  const scriptGroups = useMemo<StoryboardSceneGroup[]>(() => (workbench.episodeScript?.scenes ?? []).map((scene, index) => ({
    scene_id: scene.id, scene_no: index + 1, display_code: `S${String(index + 1).padStart(2, "0")}`,
    title: scene.title || scene.location || `场次 ${index + 1}`,
    script_duration_seconds: scene.effective_duration_seconds, shots_duration_seconds: 0,
    duration_deviation_percent: -100, status: "draft", shots: []
  })), [workbench.episodeScript]);
  const groups = storyboard?.scene_groups ?? scriptGroups;
  const allShots = useMemo(() => groups.flatMap((group) => group.shots), [groups]);
  const selectedShot = allShots.find((shot) => shot.id === selectedId) ?? null;
  const isDirty = draft !== null && JSON.stringify(cleanPayload(draft)) !== savedDraft;
  const currentScript = workbench.episodeScript;
  const sourceMismatch = Boolean(
    storyboard && currentScript && (
      storyboard.source_script_id !== currentScript.id ||
      storyboard.source_script_version !== currentScript.version ||
      storyboard.source_script_status !== currentScript.status
    )
  );

  const setUrlShot = useCallback((id: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (id) params.set("shot_id", id); else params.delete("shot_id");
    router.replace(`?${params.toString()}`, { scroll: false });
  }, [router, searchParams]);

  const selectImmediately = useCallback((id: string) => {
    setSelectedId(id);
    setUrlShot(id);
    setNavOpen(false);
  }, [setUrlShot]);

  const load = useCallback(async (preferredId?: string) => {
    setLoading(true); setError("");
    try {
      const next = await getProjectStoryboard(workbench.projectId, workbench.selectedEpisodeNo);
      setStoryboard(next);
      const shots = next?.scene_groups.flatMap((group) => group.shots) ?? [];
      const urlId = preferredId || searchParams.get("shot_id") || "";
      const fallback = shots.find((shot) => shot.status === "needs_review" || shot.source_status !== "valid") ?? shots[0];
      const nextId = shots.some((shot) => shot.id === urlId) ? urlId : fallback?.id ?? "";
      setSelectedId(nextId);
      setUrlShot(nextId);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "读取分镜失败");
    } finally { setLoading(false); }
  }, [searchParams, setUrlShot, workbench.projectId, workbench.selectedEpisodeNo]);

  useEffect(() => { void load(); }, [workbench.selectedEpisodeNo]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!selectedShot) { setDraft(null); setSavedDraft(""); return; }
    const next = payloadFromShot(selectedShot);
    setDraft(next); setSavedDraft(JSON.stringify(cleanPayload(next)));
  }, [selectedShot]);
  useEffect(() => {
    void listModelConfigs("video").then(setVideoConfigs).catch(() => setVideoConfigs([]));
  }, []);
  const loadVideoGenerations = useCallback(async (shotId?: string) => {
    if (!shotId) { setVideoGenerations([]); return; }
    setVideoLoading(true);
    try {
      setVideoGenerations(await listShotVideoGenerations(workbench.projectId, workbench.selectedEpisodeNo, shotId));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "读取视频生成记录失败");
    } finally { setVideoLoading(false); }
  }, [workbench.projectId, workbench.selectedEpisodeNo]);
  useEffect(() => { void loadVideoGenerations(selectedShot?.id); }, [selectedShot?.id, loadVideoGenerations]);
  useEffect(() => { setVideoOptions(defaultVideoGenerationOptions); }, [selectedShot?.id]);
  useEffect(() => {
    const protect = (event: BeforeUnloadEvent) => { if (isDirty) { event.preventDefault(); event.returnValue = ""; } };
    window.addEventListener("beforeunload", protect);
    return () => window.removeEventListener("beforeunload", protect);
  }, [isDirty]);
  useEffect(() => {
    const handleStageSwitch = (event: Event) => requestSwitch({ kind: "stage", stage: (event as CustomEvent<Stage>).detail });
    window.addEventListener("storyboard-stage-switch", handleStageSwitch);
    return () => window.removeEventListener("storyboard-stage-switch", handleStageSwitch);
  });

  const save = async () => {
    if (!selectedShot || !draft) return false;
    setSaving(true); setError("");
    try {
      const saved = await updateProjectStoryboardShot(workbench.projectId, workbench.selectedEpisodeNo, selectedShot.id, cleanPayload(draft));
      await load(saved.id); setMessage(`${saved.display_code} 已保存`); return true;
    } catch (reason) { setError(reason instanceof Error ? reason.message : "保存失败"); return false; }
    finally { setSaving(false); }
  };

  const requestSwitch = (target: SwitchTarget) => {
    if (isDirty) setPendingSwitch(target);
    else applySwitch(target);
  };
  const applySwitch = (target: SwitchTarget) => {
    if (target.kind === "shot") selectImmediately(target.id);
    else if (target.kind === "episode") workbench.setSelectedEpisodeNo(target.episodeNo);
    else workbench.setActiveStage(target.stage);
    setPendingSwitch(null);
  };

  const addShot = async () => {
    const sceneId = selectedShot?.source_scene_id ?? groups.find((group) => group.scene_id)?.scene_id;
    setSaving(true); setError("");
    try {
      const shot = await createProjectStoryboardShot(workbench.projectId, workbench.selectedEpisodeNo, emptyPayload(sceneId));
      await load(shot.id); setMessage(`${shot.display_code} 已创建，请完善内容`);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "创建镜头失败"); }
    finally { setSaving(false); }
  };

  const remove = async () => {
    if (!selectedShot || !window.confirm(`删除 ${selectedShot.display_code}？`)) return;
    const index = allShots.findIndex((shot) => shot.id === selectedShot.id);
    const neighbor = allShots[index + 1] ?? allShots[index - 1];
    setSaving(true);
    try { await deleteProjectStoryboardShot(workbench.projectId, workbench.selectedEpisodeNo, selectedShot.id); await load(neighbor?.id); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "删除失败"); }
    finally { setSaving(false); }
  };

  const duplicate = async () => {
    if (!selectedShot) return;
    setSaving(true);
    try { const shot = await duplicateProjectStoryboardShot(workbench.projectId, workbench.selectedEpisodeNo, selectedShot.id); await load(shot.id); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "复制失败"); }
    finally { setSaving(false); }
  };

  const reassign = async (sceneId: string) => {
    if (!selectedShot || sceneId === selectedShot.source_scene_id) return;
    if (isDirty) { setError("请先保存当前镜头修改，再重新归属场次。"); return; }
    setSaving(true); setError("");
    try {
      const moved = await reassignProjectStoryboardShot(workbench.projectId, workbench.selectedEpisodeNo, selectedShot.id, sceneId);
      await load(moved.id);
      const removedCharacterCount = Math.max(0, (selectedShot.character_snapshot_ids?.length ?? 0) - (moved.character_snapshot_ids?.length ?? 0));
      setMessage(removedCharacterCount ? `${moved.display_code} 已重新归属，已移除 ${removedCharacterCount} 个不属于新场次的出镜人物，请复核。` : `${moved.display_code} 已重新归属`);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "重新归属失败"); }
    finally { setSaving(false); }
  };

  const move = async (group: StoryboardSceneGroup, shotId: string, delta: number) => {
    if (!group.scene_id) return;
    const ids = group.shots.map((shot) => shot.id);
    const from = ids.indexOf(shotId); const to = from + delta;
    if (to < 0 || to >= ids.length) return;
    [ids[from], ids[to]] = [ids[to], ids[from]];
    try { const next = await reorderProjectStoryboardScene(workbench.projectId, workbench.selectedEpisodeNo, group.scene_id, ids); setStoryboard(next); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "排序失败"); }
  };

  const generateScene = async (sceneId: string) => {
    setGenerationStates((current) => ({ ...current, [sceneId]: "running" }));
    try {
      await generateProjectStoryboardScene(workbench.projectId, workbench.selectedEpisodeNo, sceneId);
      setGenerationStates((current) => ({ ...current, [sceneId]: "succeeded" }));
      return true;
    } catch (reason) {
      setGenerationStates((current) => ({ ...current, [sceneId]: "failed" }));
      setError(reason instanceof Error ? reason.message : "场次生成失败");
      return false;
    }
  };

  const generateEpisode = async () => {
    const targets = groups.filter((group) => group.scene_id && group.shots.length === 0);
    if (!targets.length) { setMessage("所有场次已有镜头；为避免覆盖人工修改，本次未重新生成。"); return; }
    setMessage(""); setError("");
    let succeeded = 0;
    for (const group of targets) if (group.scene_id && await generateScene(group.scene_id)) succeeded += 1;
    await load();
    setMessage(`整集生成完成：${succeeded}/${targets.length} 个场次成功；失败场次可在左侧重试。`);
  };

  const createVideo = async () => {
    if (!selectedShot) return;
    setVideoBusy(true); setError(""); setMessage("");
    try {
      const created = await createShotVideoGeneration(
        workbench.projectId,
        workbench.selectedEpisodeNo,
        selectedShot.id,
        videoCreatePayload(videoOptions)
      );
      await loadVideoGenerations(selectedShot.id);
      setMessage(created.status === "failed" ? "视频生成任务失败，请查看失败原因。" : "视频生成任务已创建。");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "创建视频生成任务失败"); }
    finally { setVideoBusy(false); }
  };

  const refreshVideo = async (generationId: string) => {
    if (!selectedShot) return;
    setVideoBusy(true); setError("");
    try {
      await refreshShotVideoGeneration(workbench.projectId, workbench.selectedEpisodeNo, selectedShot.id, generationId);
      await loadVideoGenerations(selectedShot.id);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "刷新视频生成状态失败"); }
    finally { setVideoBusy(false); }
  };

  const adoptVideo = async (generationId: string) => {
    if (!selectedShot) return;
    setVideoBusy(true); setError("");
    try {
      await adoptShotVideoGeneration(workbench.projectId, workbench.selectedEpisodeNo, selectedShot.id, generationId);
      await loadVideoGenerations(selectedShot.id);
      setMessage("已采用该视频结果。");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "采用视频结果失败"); }
    finally { setVideoBusy(false); }
  };

  const cancelVideo = async (generationId: string) => {
    if (!selectedShot) return;
    setVideoBusy(true); setError("");
    try {
      await cancelShotVideoGeneration(workbench.projectId, workbench.selectedEpisodeNo, selectedShot.id, generationId);
      await loadVideoGenerations(selectedShot.id);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "取消视频生成任务失败"); }
    finally { setVideoBusy(false); }
  };

  const update = (field: keyof ProjectStoryboardShotPayload, value: unknown) => setDraft((current) => current ? ({ ...current, [field]: value }) : current);
  const updatePrompt = (field: string, value: string) => setDraft((current) => current ? ({ ...current, prompt: { ...current.prompt, reference_asset_ids: current.prompt?.reference_asset_ids ?? [], [field]: value } }) : current);
  const selectedIndex = allShots.findIndex((shot) => shot.id === selectedId);
  const continuity = allShots.slice(Math.max(0, selectedIndex - 2), selectedIndex + 3);
  const selectedSourceScene = currentScript?.scenes.find((scene) => scene.id === draft?.source_scene_id);
  const allowedCharacterIds = selectedSourceScene?.character_snapshot_ids ?? [];
  const characterCandidates = draft?.source_scene_id
    ? workbench.characterSnapshots.filter((character) => allowedCharacterIds.includes(character.id))
    : workbench.characterSnapshots;

  const navigator = <ShotNavigator groups={groups} selectedId={selectedId} query={query} filter={filter} collapsed={collapsed} generationStates={generationStates}
    onQuery={setQuery} onFilter={setFilter} onToggle={(key) => setCollapsed((current) => { const next = new Set(current); next.has(key) ? next.delete(key) : next.add(key); return next; })}
    onSelect={(id) => requestSwitch({ kind: "shot", id })} onMove={move} onGenerate={(sceneId) => void generateScene(sceneId).then((ok) => ok ? load() : undefined)} />;

  return (
    <section className="overflow-hidden rounded-xl border bg-background shadow-sm">
      <header className="flex min-h-16 flex-wrap items-center gap-3 border-b bg-background/95 px-4 py-2 backdrop-blur">
        <Button className="xl:hidden" size="icon" variant="outline" onClick={() => setNavOpen(true)} aria-label="打开镜头导航"><Menu /></Button>
        <EpisodePicker episodeCount={workbench.project?.episode_count ?? 1} value={workbench.selectedEpisodeNo} onChange={(episodeNo) => requestSwitch({ kind: "episode", episodeNo })} />
        <div className="h-7 w-px bg-border" />
        <Metric label="来源剧本" value={storyboard?.source_script_version ? `v${storyboard.source_script_version}` : "未关联"} />
        <Metric label="当前剧本" value={currentScript ? `v${currentScript.version}` : "未创建"} />
        <Metric label="状态" value={storyboard ? statusLabels[storyboard.status] : "未创建"} />
        <Metric label="镜头" value={`${allShots.length}`} />
        <Metric label="总时长" value={`${(storyboard?.total_duration_seconds ?? 0).toFixed(1)}s`} />
        <div className="ml-auto flex gap-2">
          <Button variant="outline" onClick={() => void generateEpisode()} disabled={Object.values(generationStates).includes("running")}>生成整集分镜</Button>
          <Button onClick={() => void addShot()} disabled={saving || groups.length === 0}><Plus />新增镜头</Button>
        </div>
      </header>
      {(error || message) && <div className={`border-b px-4 py-2 text-sm ${error ? "bg-destructive/5 text-destructive" : "bg-emerald-50 text-emerald-700"}`}>{error || message}</div>}
      <SourceRelationBanner storyboard={storyboard} currentScript={currentScript} sourceMismatch={sourceMismatch} />

      <div className="grid h-[calc(100vh-13.5rem)] min-h-[620px] xl:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="hidden min-h-0 border-r xl:block">{navigator}</aside>
        <main className="grid min-h-0 grid-rows-[minmax(0,1fr)_132px]">
          <div className="min-h-0 overflow-y-auto p-5">
            {loading ? <div className="flex h-full items-center justify-center text-muted-foreground">正在加载分镜...</div> : null}
            {!loading && !selectedShot ? <EmptyState hasScenes={groups.length > 0} onAdd={() => void addShot()} /> : null}
            {!loading && selectedShot && draft ? (
              <div className="mx-auto max-w-5xl space-y-5">
                <div className="flex flex-wrap items-center gap-3">
                  <div><p className="text-xs text-muted-foreground">当前镜头</p><h2 className="text-xl font-semibold">{selectedShot.display_code}</h2></div>
                  <Badge variant={selectedShot.status === "needs_review" ? "destructive" : "secondary"}>{statusLabels[selectedShot.status]}</Badge>
                  <Select value={draft.status} onValueChange={(value) => update("status", value as ShotStatus)}><SelectTrigger size="sm"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="draft">草稿</SelectItem><SelectItem value="pending_review">待审核</SelectItem><SelectItem value="confirmed">已确认</SelectItem><SelectItem value="needs_review">需检查</SelectItem></SelectContent></Select>
                  {selectedShot.prompt_freshness === "needs_update" ? <Badge variant="outline">提示词需更新</Badge> : null}
                  <div className="ml-auto flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => void duplicate()}><Copy />复制</Button>
                    <Button size="sm" variant="outline" onClick={() => void remove()}><Trash2 />删除</Button>
                    <Button size="sm" onClick={() => void save()} disabled={!isDirty || saving}><Save />{saving ? "保存中" : "保存"}</Button>
                  </div>
                </div>
                <Tabs defaultValue="visual">
                  <TabsList variant="line" className="w-full justify-start border-b">
                    <TabsTrigger value="visual">核心画面</TabsTrigger><TabsTrigger value="sound">声音</TabsTrigger>
                    <TabsTrigger value="prompt">提示词</TabsTrigger><TabsTrigger value="video">视频生成</TabsTrigger><TabsTrigger value="reference">参考与检查</TabsTrigger>
                  </TabsList>
                  <TabsContent value="visual" className="pt-5"><VisualForm draft={draft} update={update} characterCandidates={characterCandidates} unassigned={!draft.source_scene_id} /></TabsContent>
                  <TabsContent value="sound" className="pt-5"><SoundForm draft={draft} update={update} /></TabsContent>
                  <TabsContent value="prompt" className="pt-5"><PromptForm draft={draft} update={updatePrompt} /></TabsContent>
                  <TabsContent value="video" className="pt-5"><VideoGenerationPanel shot={selectedShot} draft={draft} characterSnapshots={workbench.characterSnapshots} generations={videoGenerations} videoConfigs={videoConfigs} options={videoOptions} loading={videoLoading} busy={videoBusy} isDirty={isDirty} onOptionsChange={setVideoOptions} onCreate={() => void createVideo()} onRefresh={(id) => void refreshVideo(id)} onAdopt={(id) => void adoptVideo(id)} onCancel={(id) => void cancelVideo(id)} /></TabsContent>
                  <TabsContent value="reference" className="pt-5"><ReferencePanel shot={selectedShot} groups={groups} storyboard={storyboard} script={workbench.episodeScript} characterSnapshots={workbench.characterSnapshots} onReassign={(sceneId) => void reassign(sceneId)} disabled={saving || isDirty} /></TabsContent>
                </Tabs>
              </div>
            ) : null}
          </div>
          <ContinuityStrip shots={continuity} selectedId={selectedId} groups={groups} onSelect={(id) => requestSwitch({ kind: "shot", id })} />
        </main>
      </div>

      <Sheet open={navOpen} onOpenChange={setNavOpen}><SheetContent side="left" className="w-[320px] p-0"><SheetHeader><SheetTitle>镜头导航</SheetTitle></SheetHeader>{navigator}</SheetContent></Sheet>
      <AlertDialog open={pendingSwitch !== null} onOpenChange={(open) => !open && setPendingSwitch(null)}>
        <AlertDialogContent>
          <AlertDialogHeader><AlertDialogTitle>存在未保存修改</AlertDialogTitle><AlertDialogDescription>保存当前镜头后切换，或放弃本次修改。</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter className="sm:grid sm:grid-cols-3">
            <AlertDialogCancel>取消</AlertDialogCancel>
            <Button variant="outline" onClick={() => pendingSwitch && applySwitch(pendingSwitch)}>放弃修改</Button>
            <AlertDialogAction onClick={async (event) => { event.preventDefault(); const ok = await save(); if (ok && pendingSwitch) applySwitch(pendingSwitch); }}>保存并切换</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="min-w-16"><p className="text-[11px] text-muted-foreground">{label}</p><p className="text-sm font-medium">{value}</p></div>; }

function SourceRelationBanner({ storyboard, currentScript, sourceMismatch }: { storyboard: ProjectStoryboard | null; currentScript: ProjectWorkbenchState["episodeScript"]; sourceMismatch: boolean }) {
  const sourceVersion = storyboard?.source_script_version ? `剧本 v${storyboard.source_script_version}` : "未关联剧本";
  const currentVersion = currentScript ? `当前剧本 v${currentScript.version}` : "当前剧本未创建";
  const sourceStatus = storyboard?.source_script_status ? sourceStatusLabels[storyboard.source_script_status] ?? storyboard.source_script_status : "未知";
  const currentStatus = currentScript ? sourceStatusLabels[currentScript.status] ?? currentScript.status : "未创建";
  return <div className={`border-b px-4 py-2 text-xs ${sourceMismatch || storyboard?.status === "needs_review" ? "bg-amber-50 text-amber-800" : "bg-muted/30 text-muted-foreground"}`}>
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
      <span className="font-medium text-foreground">剧本 → 分镜</span>
      <span>分镜按剧本场次分组，镜头保存剧本块引用和制作快照。</span>
      <span>{sourceVersion}（{sourceStatus}）</span>
      <span>{currentVersion}（{currentStatus}）</span>
      {sourceMismatch ? <span className="font-medium">当前剧本已变化，请复核分镜来源。</span> : null}
    </div>
  </div>;
}

function ShotNavigator({ groups, selectedId, query, filter, collapsed, generationStates, onQuery, onFilter, onToggle, onSelect, onMove, onGenerate }: {
  groups: StoryboardSceneGroup[]; selectedId: string; query: string; filter: "all" | ShotStatus; collapsed: Set<string>;
  generationStates: Record<string, "running" | "succeeded" | "failed">;
  onQuery: (value: string) => void; onFilter: (value: "all" | ShotStatus) => void; onToggle: (key: string) => void;
  onSelect: (id: string) => void; onMove: (group: StoryboardSceneGroup, id: string, delta: number) => void;
  onGenerate: (sceneId: string) => void;
}) {
  const needle = query.trim().toLowerCase();
  return <div className="flex h-full min-h-0 flex-col">
    <div className="grid grid-cols-[1fr_104px] gap-2 border-b p-3">
      <Input value={query} onChange={(event) => onQuery(event.target.value)} placeholder="搜索镜头" />
      <Select value={filter} onValueChange={(value) => onFilter(value as typeof filter)}><SelectTrigger className="w-full"><SelectValue /></SelectTrigger><SelectContent>
        <SelectItem value="all">全部状态</SelectItem><SelectItem value="needs_review">需检查</SelectItem><SelectItem value="draft">草稿</SelectItem><SelectItem value="pending_review">待审核</SelectItem><SelectItem value="confirmed">已确认</SelectItem>
      </SelectContent></Select>
    </div>
    <div className="min-h-0 flex-1 overflow-y-auto p-2">
      {groups.map((group) => {
        const key = group.scene_id ?? "unassigned";
        const shots = group.shots.filter((shot) => (filter === "all" || shot.status === filter) && (!needle || `${shot.display_code} ${shot.shot_size ?? ""} ${shot.subject_description ?? ""}`.toLowerCase().includes(needle)));
        if ((needle || filter !== "all") && shots.length === 0) return null;
        const generation = group.scene_id ? generationStates[group.scene_id] : undefined;
        return <div key={key} className="mb-2">
          <div className="flex w-full items-center rounded-md hover:bg-muted"><button className="flex min-w-0 flex-1 items-center gap-2 px-2 py-2 text-left" onClick={() => onToggle(key)}>
            {collapsed.has(key) ? <ChevronRight className="size-4" /> : <ChevronDown className="size-4" />}
            <span className="font-semibold">{group.display_code}</span><span className="min-w-0 flex-1 truncate text-xs text-muted-foreground">{group.title}</span>
            <span className="text-[11px] text-muted-foreground">{group.shots.length} · {group.shots_duration_seconds.toFixed(1)}s</span>
          </button>{generation && <span className={`mr-1 text-[10px] ${generation === "failed" ? "text-destructive" : "text-muted-foreground"}`}>{generation === "running" ? "生成中" : generation === "succeeded" ? "成功" : "失败"}</span>}{group.scene_id && (generation === "failed" || group.shots.length === 0) ? <button className="mr-1 rounded px-1.5 py-1 text-[10px] hover:bg-background" disabled={generation === "running"} onClick={() => onGenerate(group.scene_id!)}>{generation === "failed" ? "重试" : "生成"}</button> : null}</div>
          {!collapsed.has(key) && <div className="space-y-1 pl-2">{shots.map((shot, index) => <div key={shot.id} className={`group flex items-center rounded-md border ${selectedId === shot.id ? "border-primary bg-primary/5" : "border-transparent hover:bg-muted/60"}`}>
            <button className="min-w-0 flex-1 px-2 py-2 text-left" onClick={() => onSelect(shot.id)}>
              <div className="flex items-center gap-2"><strong className="text-xs">{shot.display_code}</strong><span className="text-[11px] text-muted-foreground">{shot.shot_size || "未设景别"}</span><span className="ml-auto text-[11px]">{shot.duration_seconds ?? "-"}s</span></div>
              <p className="mt-1 truncate text-xs text-muted-foreground">{shot.subject_description || shot.visual_description || "未填写主体"}</p>
            </button>
            {group.scene_id && <div className="hidden pr-1 group-hover:flex"><button aria-label="上移" disabled={index === 0} className="px-1 text-xs disabled:opacity-20" onClick={() => onMove(group, shot.id, -1)}>↑</button><button aria-label="下移" disabled={index === shots.length - 1} className="px-1 text-xs disabled:opacity-20" onClick={() => onMove(group, shot.id, 1)}>↓</button></div>}
          </div>)}</div>}
        </div>;
      })}
    </div>
  </div>;
}

function Field({ label, value, onChange, placeholder }: { label: string; value?: string; onChange: (value: string) => void; placeholder?: string }) { return <label className="flex flex-col gap-1.5 text-sm"><span className="font-medium">{label}</span><Input value={value ?? ""} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} /></label>; }
function Area({ label, value, onChange, rows = 4 }: { label: string; value?: string; onChange: (value: string) => void; rows?: number }) { return <label className="flex flex-col gap-1.5 text-sm"><span className="font-medium">{label}</span><Textarea rows={rows} value={value ?? ""} onChange={(event) => onChange(event.target.value)} /></label>; }
function textLength(value?: string) {
  return (value ?? "").trim().length;
}

function appendNegativePromptPreset(current: string | undefined, preset: string) {
  const terms = [...(current ?? "").split(/[，,、;；\n]/), ...preset.split(/[，,、;；\n]/)]
    .map((item) => item.trim())
    .filter(Boolean);
  return Array.from(new Set(terms)).join("，");
}

function NegativePromptField({ value, onChange }: { value?: string; onChange: (value: string) => void }) {
  return <section className="flex flex-col gap-3 rounded-lg border bg-background p-4">
    <div className="flex items-center justify-between gap-3">
      <div>
        <h3 className="text-sm font-semibold">负面控制</h3>
        <p className="mt-1 text-xs text-muted-foreground">保存后作为负面提示词随视频任务提交。</p>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant="outline">{textLength(value)} 字</Badge>
        <Button type="button" size="xs" variant="ghost" onClick={() => onChange("")} disabled={!value?.trim()}>清空</Button>
      </div>
    </div>
    <Textarea rows={4} value={value ?? ""} onChange={(event) => onChange(event.target.value)} />
    <div className="flex flex-col gap-2">
      <span className="text-xs font-medium text-muted-foreground">常用预设</span>
      <div className="grid gap-2 md:grid-cols-2">
        {negativePromptPresets.map((preset) => (
          <div key={preset.label} className="grid gap-2 rounded-md border bg-muted/20 p-2">
            <div className="min-w-0">
              <span className="flex items-center gap-2">
                <Badge variant="secondary">{preset.label}</Badge>
              </span>
              <span className="mt-1 block text-xs leading-5 text-muted-foreground">{preset.text}</span>
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" size="xs" variant="outline" onClick={() => onChange(appendNegativePromptPreset(value, preset.text))}>追加</Button>
              <Button type="button" size="xs" variant="ghost" onClick={() => onChange(preset.text)}>替换</Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  </section>;
}
function PresetField({ label, value, options, onChange, placeholder }: { label: string; value?: string; options: { label: string; value: string }[]; onChange: (value: string) => void; placeholder?: string }) {
  const currentValue = value ?? "";
  const knownValue = options.some((option) => option.value === currentValue);
  const isCustom = Boolean(currentValue) && !knownValue;
  const selectValue = isCustom ? customPresetValue : currentValue;
  return <label className="space-y-1.5 text-sm">
    <span className="font-medium">{label}</span>
    <SimpleSelect value={selectValue} onValueChange={(nextValue) => onChange(nextValue === customPresetValue ? (isCustom ? currentValue : "") : nextValue)} options={[...options, { label: "自定义", value: customPresetValue }]} />
    {selectValue === customPresetValue ? <Input value={isCustom ? currentValue : ""} onChange={(event) => onChange(event.target.value)} placeholder={placeholder ?? `输入自定义${label}`} /> : null}
  </label>;
}

function VisualForm({ draft, update, characterCandidates, unassigned }: {
  draft: ProjectStoryboardShotPayload;
  update: (field: keyof ProjectStoryboardShotPayload, value: unknown) => void;
  characterCandidates: ProjectCharacterSnapshot[];
  unassigned: boolean;
}) { return <div className="grid gap-4 md:grid-cols-2">
  <PresetField label="景别" value={draft.shot_size} options={shotSizeOptions} onChange={(value) => update("shot_size", value)} placeholder="例如：极近特写" />
  <label className="space-y-1.5 text-sm"><span className="font-medium">时长（秒）</span><Input type="number" min="0.1" step="0.1" value={draft.duration_seconds ?? ""} onChange={(event) => update("duration_seconds", Number(event.target.value))} /></label>
  <CharacterAppearancePicker selectedIds={draft.character_snapshot_ids ?? []} candidates={characterCandidates} unassigned={unassigned} onChange={(ids) => update("character_snapshot_ids", ids)} />
  <Area label="主体" value={draft.subject_description} onChange={(value) => update("subject_description", value)} />
  <Area label="核心画面" value={draft.visual_description} onChange={(value) => update("visual_description", value)} />
  <Area label="动作" value={draft.action} onChange={(value) => update("action", value)} />
  <Area label="连续性备注" value={draft.continuity_note} onChange={(value) => update("continuity_note", value)} />
  <PresetField label="机位 / 角度" value={draft.camera_angle} options={cameraAngleOptions} onChange={(value) => update("camera_angle", value)} placeholder="例如：车内后视镜视角" />
  <PresetField label="运镜" value={draft.camera_movement} options={cameraMovementOptions} onChange={(value) => update("camera_movement", value)} placeholder="例如：从门缝缓慢推入" />
  <PresetField label="构图" value={draft.composition} options={compositionOptions} onChange={(value) => update("composition", value)} placeholder="例如：人物被楼梯扶手切割在画面右侧" />
  <PresetField label="表情" value={draft.expression} options={expressionOptions} onChange={(value) => update("expression", value)} placeholder="例如：强装镇定但眼神闪躲" />
  <Area label="环境" value={draft.environment} onChange={(value) => update("environment", value)} rows={3} />
  <Field label="道具（逗号分隔）" value={(draft.props ?? []).join("，")} onChange={(value) => update("props", value.split(/[，,]/).map((item) => item.trim()).filter(Boolean))} />
</div>; }

function SoundForm({ draft, update }: { draft: ProjectStoryboardShotPayload; update: (field: keyof ProjectStoryboardShotPayload, value: unknown) => void }) { return <div className="grid gap-4 md:grid-cols-2">
  <Area label="对白" value={draft.dialogue_snapshot} onChange={(value) => update("dialogue_snapshot", value)} />
  <Area label="旁白" value={draft.voiceover_snapshot} onChange={(value) => update("voiceover_snapshot", value)} />
  <Area label="音效" value={draft.sound_effect} onChange={(value) => update("sound_effect", value)} />
  <Area label="音乐" value={draft.music_note} onChange={(value) => update("music_note", value)} />
</div>; }

function PromptForm({ draft, update }: { draft: ProjectStoryboardShotPayload; update: (field: string, value: string) => void }) {
  const generationNote = draft.prompt?.video_prompt ?? "";
  const firstFrame = draft.prompt?.first_frame_description ?? "";
  const lastFrame = draft.prompt?.last_frame_description ?? "";
  return <div className="grid gap-4">
    <section className="grid gap-3 rounded-lg border bg-background p-4 lg:grid-cols-[220px_minmax(0,1fr)]">
      <div className="flex flex-wrap items-start justify-between gap-3 lg:block">
        <div>
          <h3 className="text-sm font-semibold">生成补充</h3>
          <p className="mt-1 text-xs text-muted-foreground">可选。视频生成默认使用分镜视觉字段，这里只写额外风格或模型控制。</p>
        </div>
        <Badge className="mt-2" variant={generationNote.trim() ? "secondary" : "outline"}>{textLength(generationNote)} 字</Badge>
      </div>
      <Textarea
        rows={3}
        className="min-h-24 resize-y text-sm leading-6"
        value={generationNote}
        onChange={(event) => update("video_prompt", event.target.value)}
      />
    </section>
    <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
      <section className="flex flex-col gap-3 rounded-lg border bg-background p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold">首尾帧约束</h3>
            <p className="mt-1 text-xs text-muted-foreground">用于稳定镜头开始和结束画面。</p>
          </div>
          <Badge variant="outline">{[firstFrame, lastFrame].filter((item) => item.trim()).length}/2</Badge>
        </div>
        <Field label="首帧描述" value={firstFrame} onChange={(value) => update("first_frame_description", value)} />
        <Field label="尾帧描述" value={lastFrame} onChange={(value) => update("last_frame_description", value)} />
      </section>
      <NegativePromptField value={draft.prompt?.negative_prompt} onChange={(value) => update("negative_prompt", value)} />
    </div>
  </div>;
}

const videoStatusLabels: Record<ShotVideoGeneration["status"], string> = {
  queued: "排队中", running: "生成中", succeeded: "成功", failed: "失败", canceled: "已取消"
};

function videoPreviewUrl(generation: ShotVideoGeneration) {
  return resolveAssetUrl(generation.result_url || generation.local_asset_path);
}

function VideoGenerationPanel({ shot, draft, characterSnapshots, generations, videoConfigs, options, loading, busy, isDirty, onOptionsChange, onCreate, onRefresh, onAdopt, onCancel }: {
  shot: ProjectStoryboardShot; draft: ProjectStoryboardShotPayload; characterSnapshots: ProjectCharacterSnapshot[]; generations: ShotVideoGeneration[]; videoConfigs: ModelConfig[];
  options: VideoGenerationOptions; loading: boolean; busy: boolean; isDirty: boolean; onOptionsChange: (options: VideoGenerationOptions) => void;
  onCreate: () => void; onRefresh: (id: string) => void; onAdopt: (id: string) => void; onCancel: (id: string) => void;
}) {
  const [previewGeneration, setPreviewGeneration] = useState<ShotVideoGeneration | null>(null);
  const promptPreview = buildVideoPromptPreview(draft, characterSnapshots);
  const enabledVideoConfig = videoConfigs.find((config) => config.enabled);
  const adopted = generations.find((item) => item.adopted);
  const optionDuration = Number(options.duration_seconds);
  const invalidDuration = options.duration_seconds.trim() !== "" && (!Number.isFinite(optionDuration) || optionDuration <= 0 || optionDuration > 60);
  const disabledReason = isDirty ? "请先保存当前镜头修改后再生成视频。"
    : !promptPreview.hasGenerationSource ? "请先填写核心画面、主体或动作等画面描述。"
      : shot.prompt_freshness === "needs_update" ? "提示词需要更新，请先保存或确认后再生成视频。"
        : invalidDuration ? "本次生成时长需大于 0 且不超过 60 秒。"
          : options.use_reference_images && promptPreview.sendableReferenceCharacters.length === 0 ? "当前出镜角色没有可发送的公网参考图，请先确认三视图或填写公网参考图 URL。"
            : !enabledVideoConfig ? "请先在设置中启用视频生成模型。"
              : enabledVideoConfig.last_test_status !== "success" ? "请先测试并通过当前视频生成模型。"
                : "";
  const updateOption = (field: "resolution" | "aspect_ratio" | "duration_seconds", value: string) => onOptionsChange({ ...options, [field]: value });
  const updateReferenceImages = (checked: boolean) => onOptionsChange({ ...options, use_reference_images: checked });
  const defaultDuration = `${Math.max(1, Math.round(shot.duration_seconds || 4))}`;
  const consistencyWarnings = [
    promptPreview.shotCharacters.length === 0 ? "当前镜头未选择出镜人物，本次不会注入人物一致性锚点，也无法发送角色参考图。" : "",
    promptPreview.missingCharacterIds.length ? `有 ${promptPreview.missingCharacterIds.length} 个出镜角色快照未加载，无法写入人物锚点。` : "",
    promptPreview.missingVisualCharacters.length ? `${promptPreview.missingVisualCharacters.map((item) => item.name).join("、")} 缺少视觉描述，人物一致性会更依赖镜头画面描述。` : "",
    promptPreview.missingReferenceCharacters.length ? `${promptPreview.missingReferenceCharacters.map((item) => item.name).join("、")} 缺少参考图，本期不会阻止生成。` : "",
    options.use_reference_images && promptPreview.referenceCount > promptPreview.sendableReferenceCharacters.length ? "部分参考图不是公网 URL，本次不会发送给 Seedance。" : "",
  ].filter(Boolean);
  const previewUrl = previewGeneration ? videoPreviewUrl(previewGeneration) : "";
  return <div className="space-y-4">
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]">
      <div className="rounded-lg border p-4">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="font-semibold">本次发送给模型的内容预览</h3>
          <Badge variant="secondary">{promptPreview.promptSource}</Badge>
          <Badge className="max-w-full truncate" variant="outline">{promptPreview.shotCharacters.length ? promptPreview.shotCharacters.map((item) => item.name).join("、") : "未选出镜人物"}</Badge>
          <Badge variant="outline">参考图 {promptPreview.referenceCount}</Badge>
          {options.use_reference_images ? <Badge variant="outline">发送 {promptPreview.sendableReferenceCharacters.length}</Badge> : null}
          {shot.prompt_freshness === "needs_update" ? <Badge variant="outline">需更新</Badge> : null}
        </div>
        {consistencyWarnings.length ? <div className="mt-3 flex gap-2 rounded-md border border-dashed p-3 text-sm text-muted-foreground">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          <div>
            <p className="font-medium text-foreground">人物一致性风险提示</p>
            <p className="mt-1">{consistencyWarnings.join(" ")}</p>
          </div>
        </div> : null}
        <p className="mt-3 whitespace-pre-wrap rounded-md bg-muted/60 p-3 text-sm text-muted-foreground">{promptPreview.finalText || "暂无可用于视频生成的画面描述。"}</p>
        <p className="mt-2 text-xs text-muted-foreground">声音、对白、旁白、音效和音乐字段不会发送给文生视频模型，会留给后续配音、剪辑和合成流程。</p>
      </div>
      <div className="rounded-lg border p-4">
        <h3 className="font-semibold">视频模型</h3>
        <p className="mt-2 text-sm">{enabledVideoConfig ? enabledVideoConfig.provider_name : "未启用"}</p>
        <p className="mt-1 text-xs text-muted-foreground">{enabledVideoConfig ? `${enabledVideoConfig.model_name} · ${enabledVideoConfig.last_test_status}` : "请先到设置页配置视频模型。"}</p>
        <div className="mt-4 flex flex-col gap-3">
          <label className="flex items-start gap-3 rounded-md border bg-muted/30 p-3 text-sm">
            <Checkbox
              className="mt-0.5"
              checked={options.use_reference_images}
              onCheckedChange={(checked) => updateReferenceImages(checked === true)}
              disabled={busy}
            />
            <span>
              <span className="block font-medium">携带角色参考图</span>
              <span className="mt-1 block text-xs text-muted-foreground">
                默认关闭。开启后发送当前出镜角色的公网三视图或参考图，当前可发送 {promptPreview.sendableReferenceCharacters.length} 张。
              </span>
            </span>
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">分辨率</span>
            <SimpleSelect value={options.resolution} onValueChange={(value) => updateOption("resolution", value)} options={videoResolutionOptions} disabled={busy} />
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">画幅</span>
            <SimpleSelect value={options.aspect_ratio} onValueChange={(value) => updateOption("aspect_ratio", value)} options={videoAspectRatioOptions} disabled={busy} />
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium">时长（秒）</span>
            <Input
              type="number"
              min="0.1"
              max="60"
              step="0.1"
              value={options.duration_seconds}
              onChange={(event) => updateOption("duration_seconds", event.target.value)}
              placeholder={`默认 ${defaultDuration}`}
              disabled={busy}
              aria-invalid={invalidDuration}
            />
          </label>
        </div>
        {disabledReason ? <p className="mt-3 text-sm text-destructive">{disabledReason}</p> : null}
        <Button className="mt-4 w-full" onClick={onCreate} disabled={busy || Boolean(disabledReason)}><Play />{busy ? "处理中" : "生成视频"}</Button>
      </div>
    </div>
    {adopted ? <VideoResultCard generation={adopted} title="当前采用素材" busy={busy} onPreview={setPreviewGeneration} onRefresh={onRefresh} onAdopt={onAdopt} onCancel={onCancel} /> : <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">当前镜头还没有采用的视频素材。</div>}
    <div className="rounded-lg border">
      <div className="flex items-center justify-between border-b px-4 py-3"><h3 className="font-semibold">候选历史</h3>{loading ? <span className="text-xs text-muted-foreground">加载中...</span> : null}</div>
      <div className="divide-y">{generations.length === 0 && !loading ? <p className="p-4 text-sm text-muted-foreground">暂无视频生成记录。</p> : generations.map((generation) => <VideoResultCard key={generation.id} generation={generation} busy={busy} onPreview={setPreviewGeneration} onRefresh={onRefresh} onAdopt={onAdopt} onCancel={onCancel} />)}</div>
    </div>
    <AlertDialog open={Boolean(previewGeneration)} onOpenChange={(open) => !open && setPreviewGeneration(null)}>
      <AlertDialogContent className="max-w-[min(960px,calc(100vw-2rem))]">
        <AlertDialogHeader>
          <AlertDialogTitle>视频预览</AlertDialogTitle>
          <AlertDialogDescription>{previewGeneration ? `${videoStatusLabels[previewGeneration.status]} · ${new Date(previewGeneration.created_at).toLocaleString()}` : ""}</AlertDialogDescription>
        </AlertDialogHeader>
        <div className="overflow-hidden rounded-lg bg-black">
          {previewUrl ? <video key={previewUrl} className="aspect-video w-full" src={previewUrl} controls autoPlay poster={resolveAssetUrl(previewGeneration?.thumbnail_url)} /> : <div className="flex aspect-video items-center justify-center text-sm text-muted-foreground">暂无可预览的视频地址</div>}
        </div>
        {previewGeneration?.video_prompt_snapshot ? <p className="max-h-28 overflow-y-auto whitespace-pre-wrap rounded-md bg-muted/60 p-3 text-xs text-muted-foreground">{previewGeneration.video_prompt_snapshot}</p> : null}
        <AlertDialogFooter>
          {previewUrl ? <Button asChild variant="outline"><a href={previewUrl} target="_blank" rel="noreferrer"><ExternalLink />新窗口打开</a></Button> : null}
          <AlertDialogCancel>关闭</AlertDialogCancel>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>;
}

function VideoResultCard({ generation, title, busy, onPreview, onRefresh, onAdopt, onCancel }: {
  generation: ShotVideoGeneration; title?: string; busy: boolean; onPreview: (generation: ShotVideoGeneration) => void; onRefresh: (id: string) => void; onAdopt: (id: string) => void; onCancel: (id: string) => void;
}) {
  const previewUrl = videoPreviewUrl(generation);
  const canPreview = Boolean(previewUrl);
  const canRefreshResult = generation.status === "queued" || generation.status === "running" || (generation.status === "succeeded" && !canPreview);
  return <div className="grid gap-4 p-4 lg:grid-cols-[220px_minmax(0,1fr)]">
    <button type="button" className="group relative flex aspect-video items-center justify-center overflow-hidden rounded-md bg-muted text-left disabled:cursor-not-allowed" onClick={() => canPreview && onPreview(generation)} disabled={!canPreview}>
      {previewUrl ? <video className="h-full w-full object-cover" src={previewUrl} muted playsInline preload="metadata" poster={resolveAssetUrl(generation.thumbnail_url)} /> : generation.thumbnail_url ? <img className="h-full w-full object-cover" src={resolveAssetUrl(generation.thumbnail_url)} alt="视频缩略图" /> : <span className="text-xs text-muted-foreground">暂无预览</span>}
      {canPreview ? <span className="absolute inset-0 flex items-center justify-center bg-black/0 text-white opacity-0 transition group-hover:bg-black/35 group-hover:opacity-100"><Maximize2 />预览</span> : null}
    </button>
    <div className="min-w-0 space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <h4 className="font-semibold">{title ?? new Date(generation.created_at).toLocaleString()}</h4>
        <Badge variant={generation.status === "failed" ? "destructive" : generation.status === "succeeded" ? "secondary" : "outline"}>{videoStatusLabels[generation.status]}</Badge>
        {generation.adopted ? <Badge variant="secondary">已采用</Badge> : null}
        {generation.is_stale ? <Badge variant="outline">可能过期</Badge> : null}
      </div>
      <p className="line-clamp-3 whitespace-pre-wrap text-sm text-muted-foreground">{generation.video_prompt_snapshot}</p>
      {generation.error_message ? <p className="text-sm text-destructive">{generation.error_message}</p> : null}
      <div className="flex flex-wrap gap-2">
        {canRefreshResult ? <Button size="sm" variant="outline" onClick={() => onRefresh(generation.id)} disabled={busy}><RefreshCw />{generation.status === "succeeded" ? "刷新结果" : "刷新"}</Button> : null}
        {(generation.status === "queued" || generation.status === "running") ? <Button size="sm" variant="outline" onClick={() => onCancel(generation.id)} disabled={busy}><X />取消</Button> : null}
        {generation.status === "failed" ? <Button size="sm" variant="outline" onClick={() => onRefresh(generation.id)} disabled={busy}><RefreshCw />重试刷新</Button> : null}
        {canPreview ? <Button size="sm" variant="outline" onClick={() => onPreview(generation)} disabled={busy}><Maximize2 />预览</Button> : null}
        {generation.status === "succeeded" && !generation.adopted ? <Button size="sm" onClick={() => onAdopt(generation.id)} disabled={busy || !canPreview}><Check />采用</Button> : null}
        {previewUrl ? <Button asChild size="sm" variant="outline"><a href={previewUrl} target="_blank" rel="noreferrer"><ExternalLink />打开</a></Button> : null}
      </div>
    </div>
  </div>;
}

function ReferencePanel({ shot, groups, storyboard, script, characterSnapshots, onReassign, disabled }: {
  shot: ProjectStoryboardShot; groups: StoryboardSceneGroup[]; storyboard: ProjectStoryboard | null; script: ProjectWorkbenchState["episodeScript"];
  characterSnapshots: ProjectCharacterSnapshot[];
  onReassign: (sceneId: string) => void; disabled: boolean;
}) {
  const group = groups.find((item) => item.scene_id === shot.source_scene_id);
  const scene = script?.scenes.find((item) => item.id === shot.source_scene_id);
  const sourceBlocks = scene?.blocks.filter((block) => shot.source_block_ids?.includes(block.id)) ?? [];
  const snapshotById = new Map(characterSnapshots.map((snapshot) => [snapshot.id, snapshot]));
  const shotCharacters = (shot.character_snapshot_ids ?? []).map((id) => snapshotById.get(id)).filter(Boolean) as ProjectCharacterSnapshot[];
  const missingCharacterCount = (shot.character_snapshot_ids ?? []).filter((id) => !snapshotById.has(id)).length;
  const sourceStatus = shot.source_status === "valid" ? "有效" : shot.source_status === "changed" ? "已变化" : shot.source_status === "scene_deleted" ? "场次已删除" : "未归属";
  return <div className="grid gap-4 lg:grid-cols-2">
    <div className="rounded-lg border p-4">
      <h3 className="font-semibold">镜头来源关系</h3>
      <div className="mt-3 grid gap-2 text-sm">
        <div className="flex justify-between gap-3"><span className="text-muted-foreground">来源剧本</span><span>{storyboard?.source_script_version ? `v${storyboard.source_script_version}` : "未关联"}</span></div>
        <div className="flex justify-between gap-3"><span className="text-muted-foreground">归属场次</span><span>{group ? `${group.display_code} · ${group.title}` : "未归属"}</span></div>
        <div className="flex justify-between gap-3"><span className="text-muted-foreground">引用剧本块</span><span>{shot.source_block_ids?.length ?? 0} 个</span></div>
        <div className="flex justify-between gap-3"><span className="text-muted-foreground">来源状态</span><span>{sourceStatus}</span></div>
      </div>
      <p className="mt-3 rounded-md bg-muted/60 p-3 text-xs text-muted-foreground">镜头字段是制作快照，编辑画面、对白、提示词或视频结果不会反向修改结构化剧本。</p>
      <div className="mt-4">
        <p className="mb-1.5 text-sm font-medium">重新归属场次</p>
        <Select value={shot.source_scene_id ?? ""} onValueChange={onReassign} disabled={disabled}>
          <SelectTrigger className="w-full"><SelectValue placeholder="选择场次" /></SelectTrigger>
          <SelectContent>{groups.filter((item) => item.scene_id).map((item) => <SelectItem key={item.scene_id} value={item.scene_id!}>{item.display_code} · {item.title}</SelectItem>)}</SelectContent>
        </Select>
        {disabled && <p className="mt-1 text-xs text-muted-foreground">请先保存当前修改。</p>}
      </div>
    </div>
    <div className="rounded-lg border p-4">
      <h3 className="font-semibold">来源剧本块 · {group?.display_code ?? "未归属"}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{group?.title}</p>
      <div className="mt-4 space-y-2">
        {(sourceBlocks.length ? sourceBlocks : scene?.blocks ?? []).map((block) => <p key={block.id} className={`rounded-md p-2 text-sm ${shot.source_block_ids?.includes(block.id) ? "bg-primary/10" : "bg-muted/60"}`}><span className="mr-2 text-xs text-muted-foreground">{block.block_type}</span>{block.content || "（空）"}</p>)}
        {!scene ? <p className="text-sm text-muted-foreground">暂无来源剧本块。</p> : null}
      </div>
    </div>
    <div className="rounded-lg border p-4"><h3 className="font-semibold">连续性与检查</h3><p className="mt-2 text-sm text-muted-foreground">提示词状态：{shot.prompt_freshness}</p>{shot.status === "needs_review" && <p className="mt-2 text-sm text-destructive">该镜头需要人工检查后再确认。</p>}</div>
    <div className="rounded-lg border p-4">
      <h3 className="font-semibold">人物素材</h3>
      <p className="mt-2 text-sm text-muted-foreground">来自当前镜头的出镜人物选择，会用于视频生成的人物锚点和参考图统计。</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {shotCharacters.map((character) => <Badge key={character.id} variant="secondary">{character.name}</Badge>)}
        {missingCharacterCount ? <Badge variant="outline">缺失快照 {missingCharacterCount}</Badge> : null}
        {!shotCharacters.length && !missingCharacterCount ? <span className="text-sm text-muted-foreground">未选择出镜人物</span> : null}
      </div>
    </div>
  </div>;
}

function ContinuityStrip({ shots, selectedId, groups, onSelect }: { shots: ProjectStoryboardShot[]; selectedId: string; groups: StoryboardSceneGroup[]; onSelect: (id: string) => void }) { return <div className="border-t bg-muted/30 p-3"><div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground"><List className="size-3.5" />连续性 · 前后各 2 镜</div><div className="grid grid-cols-5 gap-2">{shots.map((shot) => { const group = groups.find((item) => item.scene_id === shot.source_scene_id); return <button key={shot.id} onClick={() => onSelect(shot.id)} className={`min-w-0 rounded-lg border p-2 text-left ${shot.id === selectedId ? "border-primary bg-background shadow-sm" : "bg-background/60 hover:bg-background"}`}><div className="flex items-center gap-1"><strong className="text-xs">{shot.display_code}</strong><span className="truncate text-[10px] text-muted-foreground">{group?.display_code}</span></div><p className="mt-1 truncate text-xs text-muted-foreground">{shot.subject_description || shot.action || "未填写摘要"}</p></button>; })}</div></div>; }

function EmptyState({ hasScenes, onAdd }: { hasScenes: boolean; onAdd: () => void }) { return <div className="flex h-full flex-col items-center justify-center gap-3 text-center"><div className="rounded-full bg-muted p-3"><List className="size-5" /></div><div><h2 className="font-semibold">当前集还没有镜头</h2><p className="mt-1 text-sm text-muted-foreground">{hasScenes ? "从首个场次创建镜头并开始逐镜精修。" : "请先完成结构化剧本场次。"}</p></div>{hasScenes && <Button onClick={onAdd}><Plus />新增镜头</Button>}</div>; }
