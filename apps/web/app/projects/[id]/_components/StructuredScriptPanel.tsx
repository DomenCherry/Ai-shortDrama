"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  BookOpenIcon,
  CheckCircle2Icon,
  CircleAlertIcon,
  CopyIcon,
  FilePlus2Icon,
  PlusIcon,
  SaveIcon,
  SparklesIcon,
  Trash2Icon
} from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  adoptProjectScriptGeneration,
  checkProjectEpisodeScript,
  confirmProjectEpisodeScript,
  createProjectScriptGeneration,
  discardProjectScriptGeneration,
  getProjectEpisodeScript,
  listProjectScriptGenerations,
  submitProjectEpisodeScript,
  updateProjectEpisodeScript,
  type ProjectEpisodeScript,
  type ScriptBlockPayload,
  type ScriptCheckIssue,
  type ScriptGeneration,
  type ScriptGenerationScope,
  type ScriptInteriorExterior,
  type ScriptRewritePreset,
  type ScriptScenePayload,
  type ScriptTimeOfDay
} from "@/lib/api";
import type { ProjectWorkbenchState } from "../_hooks/useProjectWorkbench";
import { ArtifactStatusBadge, EpisodePicker, ProductionContextSummary } from "./shared";

type LocalBlock = ScriptBlockPayload & { _key: string };
type LocalScene = Omit<ScriptScenePayload, "blocks"> & { _key: string; blocks: LocalBlock[] };
type MutateScenes = (updater: (current: LocalScene[]) => LocalScene[]) => void;
type SupportTab = "source" | "issues" | "history";

const blockLabels = { action: "动作", dialogue: "对白", voiceover: "旁白", transition: "转场" } as const;
const timeLabels: Record<ScriptTimeOfDay, string> = { morning: "早晨", day: "白天", dusk: "黄昏", night: "夜晚", other: "其他" };
const interiorLabels: Record<ScriptInteriorExterior, string> = { interior: "内景", exterior: "外景", mixed: "混合" };
const presetLabels: Record<ScriptRewritePreset, string> = {
  more_satisfying: "更爽",
  more_tragic: "更虐",
  more_suspenseful: "更悬疑",
  more_colloquial: "更口语化",
  short_video_pacing: "更短视频化",
  compress_duration: "压缩时长",
  stronger_cliffhanger: "增强结尾悬念"
};

function localKey(prefix: string) {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return `${prefix}-${crypto.randomUUID()}`;
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function emptyBlock(type: ScriptBlockPayload["block_type"] = "action"): LocalBlock {
  return { _key: localKey("block"), block_type: type, content: "" };
}

function emptyScene(): LocalScene {
  return {
    _key: localKey("scene"),
    title: "",
    location: "",
    time_of_day: "day",
    interior_exterior: "interior",
    character_snapshot_ids: [],
    story_purpose: "",
    blocks: [emptyBlock()]
  };
}

function scriptToLocal(script: ProjectEpisodeScript | null): { title: string; manualDuration: string; scenes: LocalScene[] } {
  if (!script) return { title: "", manualDuration: "", scenes: [] };
  return {
    title: script.title ?? "",
    manualDuration: script.manual_duration_seconds ? String(script.manual_duration_seconds) : "",
    scenes: script.scenes.map((scene) => ({
      _key: scene.id,
      id: scene.id,
      title: scene.title ?? "",
      location: scene.location ?? "",
      time_of_day: scene.time_of_day,
      interior_exterior: scene.interior_exterior,
      character_snapshot_ids: scene.character_snapshot_ids,
      manual_duration_seconds: scene.manual_duration_seconds,
      story_purpose: scene.story_purpose ?? "",
      blocks: scene.blocks.map((block) => ({
        _key: block.id,
        id: block.id,
        block_type: block.block_type,
        character_snapshot_id: block.character_snapshot_id,
        temporary_speaker_name: block.temporary_speaker_name ?? "",
        content: block.content ?? "",
        emotion: block.emotion ?? "",
        performance_note: block.performance_note ?? ""
      }))
    }))
  };
}

function cleanText(value?: string) {
  return value?.trim() || undefined;
}

function localToPayload(revision: number | null, title: string, manualDuration: string, scenes: LocalScene[]) {
  const duration = Number(manualDuration);
  return {
    revision,
    title: cleanText(title),
    manual_duration_seconds: manualDuration && Number.isFinite(duration) ? duration : undefined,
    scenes: scenes.map((scene) => ({
      id: scene.id,
      title: cleanText(scene.title),
      location: cleanText(scene.location),
      time_of_day: scene.time_of_day,
      interior_exterior: scene.interior_exterior,
      character_snapshot_ids: scene.character_snapshot_ids,
      manual_duration_seconds: scene.manual_duration_seconds,
      story_purpose: cleanText(scene.story_purpose),
      blocks: scene.blocks.map((block) => ({
        id: block.id,
        block_type: block.block_type,
        character_snapshot_id: block.block_type === "dialogue" ? block.character_snapshot_id : undefined,
        temporary_speaker_name: block.block_type === "dialogue" ? cleanText(block.temporary_speaker_name) : undefined,
        content: cleanText(block.content),
        emotion: cleanText(block.emotion),
        performance_note: cleanText(block.performance_note)
      }))
    }))
  };
}

function formatDuration(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const rest = Math.round(seconds % 60);
  return minutes ? `${minutes} 分 ${rest} 秒` : `${rest} 秒`;
}

function selectedKeyAfterRefresh(selectedKey: string, previous: LocalScene[], next: LocalScene[]) {
  const previousIndex = previous.findIndex((scene) => scene._key === selectedKey);
  const previousScene = previous[previousIndex];
  const matchingScene = previousScene?.id ? next.find((scene) => scene.id === previousScene.id) : null;
  return matchingScene?._key ?? next[Math.min(Math.max(previousIndex, 0), Math.max(next.length - 1, 0))]?._key ?? "";
}

export function StructuredScriptPanel({ workbench }: { workbench: ProjectWorkbenchState }) {
  const project = workbench.project;
  const [script, setScript] = useState<ProjectEpisodeScript | null>(null);
  const [title, setTitle] = useState("");
  const [manualDuration, setManualDuration] = useState("");
  const [scenes, setScenes] = useState<LocalScene[]>([]);
  const [generations, setGenerations] = useState<ScriptGeneration[]>([]);
  const [selectedBlocks, setSelectedBlocks] = useState<string[]>([]);
  const [issues, setIssues] = useState<ScriptCheckIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [dirty, setDirty] = useState(false);
  const [pendingEpisode, setPendingEpisode] = useState<number | null>(null);
  const [generationOpen, setGenerationOpen] = useState(false);
  const [generationScope, setGenerationScope] = useState<ScriptGenerationScope>("episode");
  const [generationSceneId, setGenerationSceneId] = useState<string>();
  const [instruction, setInstruction] = useState("");
  const [preset, setPreset] = useState<ScriptRewritePreset | "none">("none");
  const [activeGeneration, setActiveGeneration] = useState<ScriptGeneration | null>(null);
  const [deleteSceneIndex, setDeleteSceneIndex] = useState<number | null>(null);
  const [selectedSceneKey, setSelectedSceneKey] = useState("");
  const [supportOpen, setSupportOpen] = useState(false);
  const [supportTab, setSupportTab] = useState<SupportTab>("source");

  const load = useCallback(async () => {
    if (!project) return;
    setLoading(true);
    setError("");
    try {
      const [nextScript, nextGenerations] = await Promise.all([
        getProjectEpisodeScript(workbench.projectId, workbench.selectedEpisodeNo),
        listProjectScriptGenerations(workbench.projectId, workbench.selectedEpisodeNo)
      ]);
      const local = scriptToLocal(nextScript);
      setScript(nextScript);
      setTitle(local.title);
      setManualDuration(local.manualDuration);
      setScenes(local.scenes);
      setSelectedSceneKey(local.scenes[0]?._key ?? "");
      setGenerations(nextGenerations);
      setIssues(nextScript?.validation_issues ?? []);
      setSelectedBlocks([]);
      setDirty(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "剧本加载失败");
    } finally {
      setLoading(false);
    }
  }, [project, workbench.projectId, workbench.selectedEpisodeNo]);

  useEffect(() => void load(), [load]);

  useEffect(() => {
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (!dirty) return;
      event.preventDefault();
    };
    window.addEventListener("beforeunload", beforeUnload);
    return () => window.removeEventListener("beforeunload", beforeUnload);
  }, [dirty]);

  const mutateScenes = (updater: (current: LocalScene[]) => LocalScene[]) => {
    setScenes(updater);
    setDirty(true);
    setMessage("");
  };

  const selectedRange = useMemo(() => {
    for (const scene of scenes) {
      const positions = selectedBlocks.map((id) => scene.blocks.findIndex((block) => block._key === id)).filter((index) => index >= 0).sort((a, b) => a - b);
      if (positions.length === selectedBlocks.length && positions.length > 0 && positions.every((position, index) => position === positions[0] + index)) {
        return { sceneId: scene.id, blockIds: positions.map((position) => scene.blocks[position].id).filter((id): id is string => Boolean(id)) };
      }
    }
    return null;
  }, [scenes, selectedBlocks]);

  if (!project) return null;

  const save = async () => {
    setBusy("save");
    setError("");
    setMessage("");
    try {
      const saved = await updateProjectEpisodeScript(
        workbench.projectId,
        workbench.selectedEpisodeNo,
        localToPayload(script?.revision ?? null, title, manualDuration, scenes)
      );
      const local = scriptToLocal(saved);
      const nextSelectedKey = selectedKeyAfterRefresh(selectedSceneKey, scenes, local.scenes);
      setScript(saved);
      setTitle(local.title);
      setManualDuration(local.manualDuration);
      setScenes(local.scenes);
      setSelectedSceneKey(nextSelectedKey);
      setIssues(saved.validation_issues);
      setDirty(false);
      setMessage("剧本已保存；实质变化已标记同集下游内容需要检查。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "剧本保存失败，你的本地修改仍保留");
    } finally {
      setBusy("");
    }
  };

  const runCheck = async () => {
    if (!script || dirty) {
      setError(dirty ? "请先保存当前修改，再执行一致性检查。" : "请先创建并保存剧本。");
      return;
    }
    setBusy("check");
    setError("");
    try {
      const result = await checkProjectEpisodeScript(workbench.projectId, workbench.selectedEpisodeNo, script.revision);
      setIssues(result.issues);
      setMessage(result.semantic_check_status === "failed" ? "结构检查已完成；语义检查暂不可用。" : "一致性检查已完成。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "一致性检查失败");
    } finally {
      setBusy("");
    }
  };

  const changeStatus = async (target: "review" | "confirm") => {
    if (!script || dirty) {
      setError(dirty ? "请先保存当前修改。" : "请先创建并保存剧本。");
      return;
    }
    setBusy(target);
    setError("");
    try {
      const saved = target === "review"
        ? await submitProjectEpisodeScript(workbench.projectId, workbench.selectedEpisodeNo, script.revision)
        : await confirmProjectEpisodeScript(workbench.projectId, workbench.selectedEpisodeNo, script.revision);
      setScript(saved);
      setIssues(saved.validation_issues);
      setMessage(target === "review" ? "剧本已提交待确认。" : "剧本已确认，可作为正式制作输入。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "剧本状态更新失败");
    } finally {
      setBusy("");
    }
  };

  const openGeneration = (scope: ScriptGenerationScope, sceneId?: string) => {
    if (dirty) {
      setError("请先保存或放弃当前修改，再生成候选内容。");
      return;
    }
    if (scope === "blocks" && (!selectedRange || selectedRange.blockIds.length !== selectedBlocks.length)) {
      setError("局部改写仅支持同一场次内已保存的连续内容块。");
      return;
    }
    setGenerationScope(scope);
    setGenerationSceneId(sceneId ?? selectedRange?.sceneId);
    setGenerationOpen(true);
    setError("");
  };

  const generate = async () => {
    setBusy("generate");
    setError("");
    try {
      const generated = await createProjectScriptGeneration(workbench.projectId, workbench.selectedEpisodeNo, {
        generation_scope: generationScope,
        target_scene_id: generationSceneId,
        target_block_ids: generationScope === "blocks" ? selectedRange?.blockIds ?? [] : [],
        rewrite_preset: preset === "none" ? undefined : preset,
        instruction: cleanText(instruction),
        client_request_id: localKey("script-generation"),
        base_script_version: script?.version ?? null,
        base_script_revision: script?.revision ?? null
      });
      setGenerations((current) => [generated, ...current.filter((item) => item.id !== generated.id)]);
      setActiveGeneration(generated);
      setGenerationOpen(false);
      setMessage("候选已生成，采用前不会修改正式剧本。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "候选剧本生成失败");
    } finally {
      setBusy("");
    }
  };

  const adopt = async () => {
    if (!activeGeneration) return;
    setBusy("adopt");
    setError("");
    try {
      const result = await adoptProjectScriptGeneration(workbench.projectId, workbench.selectedEpisodeNo, activeGeneration.id, script?.revision ?? null);
      const local = scriptToLocal(result.script);
      const nextSelectedKey = selectedKeyAfterRefresh(selectedSceneKey, scenes, local.scenes);
      setScript(result.script);
      setTitle(local.title);
      setManualDuration(local.manualDuration);
      setScenes(local.scenes);
      setSelectedSceneKey(nextSelectedKey);
      setIssues(result.script.validation_issues);
      setGenerations((current) => current.map((item) => item.id === result.generation.id ? result.generation : item));
      setActiveGeneration(null);
      setSelectedBlocks([]);
      setDirty(false);
      setMessage("候选已采用，正式剧本已生成新版本。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "候选采用失败");
    } finally {
      setBusy("");
    }
  };

  const discard = async () => {
    if (!activeGeneration) return;
    setBusy("discard");
    try {
      const discarded = await discardProjectScriptGeneration(workbench.projectId, workbench.selectedEpisodeNo, activeGeneration.id);
      setGenerations((current) => current.map((item) => item.id === discarded.id ? discarded : item));
      setActiveGeneration(null);
      setMessage("候选已放弃，正式剧本未发生变化。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "候选放弃失败");
    } finally {
      setBusy("");
    }
  };

  const requestEpisodeChange = (episode: number) => {
    if (!dirty) {
      workbench.setSelectedEpisodeNo(episode);
      return;
    }
    setPendingEpisode(episode);
  };

  const moveScene = (index: number, delta: number) => mutateScenes((current) => {
    const target = index + delta;
    if (target < 0 || target >= current.length) return current;
    const next = [...current];
    [next[index], next[target]] = [next[target], next[index]];
    return next;
  });

  const addScene = () => {
    const scene = emptyScene();
    mutateScenes((current) => [...current, scene]);
    setSelectedSceneKey(scene._key);
    setSelectedBlocks([]);
  };

  const duplicateScene = (sceneIndex: number) => {
    const source = scenes[sceneIndex];
    if (!source) return;
    const clone: LocalScene = {
      ...source,
      _key: localKey("scene"),
      id: undefined,
      blocks: source.blocks.map((block) => ({ ...block, _key: localKey("block"), id: undefined }))
    };
    mutateScenes((current) => [...current.slice(0, sceneIndex + 1), clone, ...current.slice(sceneIndex + 1)]);
    setSelectedSceneKey(clone._key);
    setSelectedBlocks([]);
  };

  const confirmDeleteScene = () => {
    if (deleteSceneIndex === null) return;
    const deleted = scenes[deleteSceneIndex];
    const nextSelected = scenes[deleteSceneIndex + 1] ?? scenes[deleteSceneIndex - 1];
    mutateScenes((current) => current.filter((_, index) => index !== deleteSceneIndex));
    if (deleted?._key === selectedSceneKey) setSelectedSceneKey(nextSelected?._key ?? "");
    if (deleted) {
      const deletedBlockKeys = new Set(deleted.blocks.map((block) => block._key));
      setSelectedBlocks((current) => current.filter((key) => !deletedBlockKeys.has(key)));
    }
    setDeleteSceneIndex(null);
  };

  const selectedSceneIndex = scenes.findIndex((scene) => scene._key === selectedSceneKey);
  const selectedScene = selectedSceneIndex >= 0 ? scenes[selectedSceneIndex] : null;

  return (
    <section className="structured-script-workbench">
      <div className="structured-script-toolbar">
        <div className="structured-script-episode">
          <EpisodePicker episodeCount={project.episode_count} value={workbench.selectedEpisodeNo} onChange={requestEpisodeChange} />
          {script ? <ArtifactStatusBadge status={script.status} /> : <Badge variant="outline">未开始</Badge>}
          {script ? <span className="hint">v{script.version} · 修订 {script.revision}</span> : null}
        </div>
        <div className="structured-script-duration" aria-label="剧本时长">
          <span>目标 {formatDuration((project.episode_duration || 0) * 60)}</span>
          <strong>{script ? formatDuration(script.effective_duration_seconds) : "尚未估算"}</strong>
          {script ? <Badge variant={Math.abs(script.duration_deviation_percent) > 10 ? "destructive" : "secondary"}>{script.duration_deviation_percent > 0 ? "+" : ""}{script.duration_deviation_percent}%</Badge> : null}
        </div>
        <div className="structured-script-actions">
          <Button type="button" variant="secondary" onClick={() => setSupportOpen(true)}>
            <BookOpenIcon data-icon="inline-start" />参考与检查
            {issues.length ? <Badge variant={issues.some((issue) => issue.severity === "error") ? "destructive" : "outline"}>{issues.length}</Badge> : null}
          </Button>
          <Button type="button" variant="secondary" onClick={() => openGeneration("episode")} disabled={Boolean(busy) || !workbench.episodeContent?.detailed_content}>
            <SparklesIcon data-icon="inline-start" />生成整集
          </Button>
          <Button type="button" variant="secondary" onClick={runCheck} disabled={Boolean(busy) || !script || dirty}>{busy === "check" ? "检查中..." : "检查"}</Button>
          <Button type="button" onClick={save} disabled={Boolean(busy) || !dirty}>
            <SaveIcon data-icon="inline-start" />{busy === "save" ? "保存中..." : "保存"}
          </Button>
          <Button type="button" variant="secondary" onClick={() => changeStatus("review")} disabled={Boolean(busy) || !script || dirty}>提交待确认</Button>
          <Button type="button" onClick={() => changeStatus("confirm")} disabled={Boolean(busy) || !script || dirty}>确认剧本</Button>
        </div>
      </div>

      {error ? <Alert variant="destructive"><CircleAlertIcon /><AlertTitle>操作未完成</AlertTitle><AlertDescription>{error}</AlertDescription></Alert> : null}
      {message ? <Alert><CheckCircle2Icon /><AlertTitle>状态更新</AlertTitle><AlertDescription>{message}</AlertDescription></Alert> : null}
      {!workbench.episodeContent?.detailed_content ? (
        <Alert><CircleAlertIcon /><AlertTitle>缺少单集故事正文</AlertTitle><AlertDescription>整集生成暂不可用。你仍可人工创建空白草稿，或先返回故事文本完成正文。</AlertDescription></Alert>
      ) : null}

      <ProductionContextSummary
        worldSnapshots={workbench.worldSnapshots}
        characterSnapshots={workbench.characterSnapshots}
        storyOutlineStatus={workbench.storyOutlineStatus}
        episodeOutline={workbench.selectedEpisodeOutline}
        episodeContentStatus={workbench.episodeContentStatus}
        projectId={workbench.projectId}
      />

      {loading ? (
        <div className="structured-script-loading"><Skeleton className="h-12 w-full" /><Skeleton className="h-64 w-full" /></div>
      ) : (
        <div className="structured-script-editor">
          <div className="structured-script-meta">
            <div className="field"><Label htmlFor="script-title">剧本标题</Label><Input id="script-title" value={title} maxLength={120} placeholder={workbench.selectedEpisodeOutline?.title || "沿用分集标题"} onChange={(event) => { setTitle(event.target.value); setDirty(true); }} /></div>
            <div className="field"><Label htmlFor="script-duration">人工总时长（秒）</Label><Input id="script-duration" type="number" min="0.1" max="3600" step="0.1" value={manualDuration} placeholder="留空使用场次汇总" onChange={(event) => { setManualDuration(event.target.value); setDirty(true); }} /></div>
          </div>

          {scenes.length ? (
            <div className="structured-script-layout">
              <SceneNavigator scenes={scenes} script={script} issues={issues} selectedKey={selectedSceneKey} onSelect={(key) => { setSelectedSceneKey(key); setSelectedBlocks([]); }} onAdd={addScene} />
              {selectedScene ? (
                <SceneDetail
                  scene={selectedScene}
                  sceneIndex={selectedSceneIndex}
                  sceneCount={scenes.length}
                  script={script}
                  workbench={workbench}
                  selectedBlocks={selectedBlocks}
                  setSelectedBlocks={setSelectedBlocks}
                  mutateScenes={mutateScenes}
                  onMove={moveScene}
                  onDuplicate={() => duplicateScene(selectedSceneIndex)}
                  onRewrite={() => openGeneration("scene", selectedScene.id)}
                  onDelete={() => setDeleteSceneIndex(selectedSceneIndex)}
                  onRewriteBlocks={() => openGeneration("blocks")}
                  canRewriteBlocks={Boolean(selectedRange)}
                />
              ) : null}
            </div>
          ) : (
            <div className="structured-script-empty">
              <FilePlus2Icon />
              <div><h3>当前集还没有正式剧本</h3><p>从故事正文生成候选，或创建空白场次开始人工整理。</p></div>
              <Button type="button" variant="secondary" onClick={addScene}><PlusIcon data-icon="inline-start" />创建空白场次</Button>
            </div>
          )}
        </div>
      )}

      <ScriptSupportDrawer
        open={supportOpen}
        onOpenChange={setSupportOpen}
        activeTab={supportTab}
        onTabChange={setSupportTab}
        projectId={workbench.projectId}
        episodeNo={workbench.selectedEpisodeNo}
        content={workbench.episodeContent}
        issues={issues}
        generations={generations}
        onOpenGeneration={(generation) => { setSupportOpen(false); setActiveGeneration(generation); }}
      />

      <Sheet open={generationOpen} onOpenChange={setGenerationOpen}>
        <SheetContent className="structured-script-sheet sm:max-w-xl">
          <SheetHeader><SheetTitle>{generationScope === "episode" ? "生成整集结构化剧本" : generationScope === "scene" ? "重新生成场次" : "局部改写内容块"}</SheetTitle><SheetDescription>生成结果先保存为候选，采用前不会覆盖正式剧本。</SheetDescription></SheetHeader>
          <div className="sheet-form-body">
            <div className="field"><Label>改写方向</Label><Select value={preset} onValueChange={(value: ScriptRewritePreset | "none") => setPreset(value)}><SelectTrigger className="w-full"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="none">不使用预设</SelectItem>{Object.entries(presetLabels).map(([value, label]) => <SelectItem key={value} value={value}>{label}</SelectItem>)}</SelectContent></Select></div>
            <div className="field"><Label htmlFor="script-instruction">自定义指令</Label><Textarea id="script-instruction" value={instruction} maxLength={2000} rows={6} placeholder="例如：压缩对白，保留反转，并加强结尾悬念。" onChange={(event) => setInstruction(event.target.value)} /></div>
          </div>
          <SheetFooter><Button type="button" variant="secondary" onClick={() => setGenerationOpen(false)}>取消</Button><Button type="button" onClick={generate} disabled={busy === "generate"}><SparklesIcon data-icon="inline-start" />{busy === "generate" ? "生成中..." : "生成候选"}</Button></SheetFooter>
        </SheetContent>
      </Sheet>

      <Sheet open={Boolean(activeGeneration)} onOpenChange={(open) => !open && setActiveGeneration(null)}>
        <SheetContent className="structured-script-sheet sm:max-w-2xl">
          <SheetHeader><SheetTitle>候选预览</SheetTitle><SheetDescription>{activeGeneration ? `${activeGeneration.generation_scope === "episode" ? "整集" : activeGeneration.generation_scope === "scene" ? "场次" : "局部"}候选 · ${activeGeneration.status === "candidate" ? "待处理" : activeGeneration.status === "adopted" ? "已采用" : "已放弃"}` : ""}</SheetDescription></SheetHeader>
          <div className="candidate-preview">{activeGeneration ? <CandidatePreview generation={activeGeneration} /> : null}</div>
          <SheetFooter>{activeGeneration?.status === "candidate" ? <><Button type="button" variant="destructive" onClick={discard} disabled={Boolean(busy)}>放弃候选</Button><Button type="button" onClick={adopt} disabled={Boolean(busy)}>{busy === "adopt" ? "采用中..." : "采用候选"}</Button></> : <Button type="button" variant="secondary" onClick={() => setActiveGeneration(null)}>关闭</Button>}</SheetFooter>
        </SheetContent>
      </Sheet>

      <ConfirmDialog open={pendingEpisode !== null} title="切换集数？" description="当前剧本有未保存修改。切换后这些修改会丢失。" destructive confirmLabel="放弃修改并切换" onOpenChange={(open) => !open && setPendingEpisode(null)} onConfirm={() => { if (pendingEpisode) workbench.setSelectedEpisodeNo(pendingEpisode); setPendingEpisode(null); }} />
      <ConfirmDialog open={deleteSceneIndex !== null} title="删除场次？" description="删除场次后，已有关联分镜将需要重新检查。此操作在保存前仍可通过刷新撤销。" destructive confirmLabel="删除场次" onOpenChange={(open) => !open && setDeleteSceneIndex(null)} onConfirm={confirmDeleteScene} />
    </section>
  );
}

function SceneNavigator({
  scenes,
  script,
  issues,
  selectedKey,
  onSelect,
  onAdd
}: {
  scenes: LocalScene[];
  script: ProjectEpisodeScript | null;
  issues: ScriptCheckIssue[];
  selectedKey: string;
  onSelect: (key: string) => void;
  onAdd: () => void;
}) {
  return (
    <nav className="script-scene-navigator" aria-label="剧本场次列表">
      <div className="script-scene-navigator-header">
        <div><h3>场次列表</h3><span>{scenes.length} 场</span></div>
        <Button type="button" size="icon-sm" variant="ghost" aria-label="新增场次" onClick={onAdd}><PlusIcon /></Button>
      </div>
      <div className="script-scene-list">
        {scenes.map((scene, index) => {
          const savedScene = scene.id ? script?.scenes.find((item) => item.id === scene.id) : null;
          const issueCount = scene.id ? issues.filter((issue) => issue.scene_id === scene.id).length : 0;
          return (
            <button type="button" key={scene._key} className="script-scene-list-item" aria-current={scene._key === selectedKey ? "true" : undefined} onClick={() => onSelect(scene._key)}>
              <span className="script-scene-list-code">S{String(index + 1).padStart(2, "0")}</span>
              <span className="script-scene-list-copy">
                <strong>{scene.title?.trim() || scene.location?.trim() || "未命名场次"}</strong>
                <small>{savedScene ? formatDuration(savedScene.effective_duration_seconds) : "未保存"} · {scene.blocks.length} 块</small>
              </span>
              {issueCount ? <Badge variant="destructive">{issueCount}</Badge> : null}
            </button>
          );
        })}
      </div>
      <Button type="button" variant="secondary" size="sm" onClick={onAdd}><PlusIcon data-icon="inline-start" />新增场次</Button>
    </nav>
  );
}

function SceneDetail({
  scene,
  sceneIndex,
  sceneCount,
  script,
  workbench,
  selectedBlocks,
  setSelectedBlocks,
  mutateScenes,
  onMove,
  onDuplicate,
  onRewrite,
  onDelete,
  onRewriteBlocks,
  canRewriteBlocks
}: {
  scene: LocalScene;
  sceneIndex: number;
  sceneCount: number;
  script: ProjectEpisodeScript | null;
  workbench: ProjectWorkbenchState;
  selectedBlocks: string[];
  setSelectedBlocks: React.Dispatch<React.SetStateAction<string[]>>;
  mutateScenes: MutateScenes;
  onMove: (index: number, delta: number) => void;
  onDuplicate: () => void;
  onRewrite: () => void;
  onDelete: () => void;
  onRewriteBlocks: () => void;
  canRewriteBlocks: boolean;
}) {
  const savedScene = scene.id ? script?.scenes.find((item) => item.id === scene.id) : null;
  return (
    <article className="script-scene script-scene-detail" aria-label={`第 ${sceneIndex + 1} 场详情`}>
      <header className="script-scene-header">
        <span className="script-scene-number">S{String(sceneIndex + 1).padStart(2, "0")}</span>
        <Input aria-label={`第 ${sceneIndex + 1} 场标题`} value={scene.title ?? ""} placeholder="场次标题（可选）" maxLength={120} onChange={(event) => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, title: event.target.value } : item))} />
        <span className="hint">{savedScene ? formatDuration(savedScene.effective_duration_seconds) : "未保存"}</span>
        <div className="script-scene-tools">
          <Button type="button" size="icon-sm" variant="ghost" aria-label="上移场次" disabled={sceneIndex === 0} onClick={() => onMove(sceneIndex, -1)}><ArrowUpIcon /></Button>
          <Button type="button" size="icon-sm" variant="ghost" aria-label="下移场次" disabled={sceneIndex === sceneCount - 1} onClick={() => onMove(sceneIndex, 1)}><ArrowDownIcon /></Button>
          <Button type="button" size="icon-sm" variant="ghost" aria-label="复制场次" onClick={onDuplicate}><CopyIcon /></Button>
          <Button type="button" size="sm" variant="secondary" disabled={!scene.id} onClick={onRewrite}><SparklesIcon data-icon="inline-start" />重写</Button>
          <Button type="button" size="icon-sm" variant="ghost" aria-label="删除场次" onClick={onDelete}><Trash2Icon /></Button>
        </div>
      </header>

      <div className="script-scene-body">
        <div className="script-scene-fields">
          <div className="field"><Label>地点</Label><Input value={scene.location ?? ""} maxLength={120} placeholder="例如：林家客厅" onChange={(event) => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, location: event.target.value } : item))} /></div>
          <div className="field"><Label>时间</Label><Select value={scene.time_of_day} onValueChange={(value: ScriptTimeOfDay) => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, time_of_day: value } : item))}><SelectTrigger className="w-full"><SelectValue /></SelectTrigger><SelectContent>{Object.entries(timeLabels).map(([value, label]) => <SelectItem key={value} value={value}>{label}</SelectItem>)}</SelectContent></Select></div>
          <div className="field"><Label>内外景</Label><Select value={scene.interior_exterior} onValueChange={(value: ScriptInteriorExterior) => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, interior_exterior: value } : item))}><SelectTrigger className="w-full"><SelectValue /></SelectTrigger><SelectContent>{Object.entries(interiorLabels).map(([value, label]) => <SelectItem key={value} value={value}>{label}</SelectItem>)}</SelectContent></Select></div>
          <div className="field"><Label>人工时长（秒）</Label><Input type="number" min="0.1" max="3600" step="0.1" value={scene.manual_duration_seconds ?? ""} placeholder="自动估算" onChange={(event) => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, manual_duration_seconds: event.target.value ? Number(event.target.value) : undefined } : item))} /></div>
        </div>

        <div className="script-character-picker" aria-label="出场人物">
          <span className="field-label">出场人物</span>
          {workbench.characterSnapshots.length ? workbench.characterSnapshots.map((character) => (
            <label key={character.id}><Checkbox checked={scene.character_snapshot_ids.includes(character.id)} onCheckedChange={(checked) => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, character_snapshot_ids: checked ? [...item.character_snapshot_ids, character.id] : item.character_snapshot_ids.filter((id) => id !== character.id) } : item))} /><span>{character.name}</span></label>
          )) : <span className="hint">项目尚未加载角色</span>}
        </div>

        <div className="field"><Label>剧情作用</Label><Textarea value={scene.story_purpose ?? ""} maxLength={1000} rows={2} placeholder="例如：揭示债务真相，推动母女冲突升级" onChange={(event) => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, story_purpose: event.target.value } : item))} /></div>

        <div className="script-block-list">
          {scene.blocks.map((block, blockIndex) => (
            <div className={`script-block script-block-${block.block_type}`} key={block._key}>
              <div className="script-block-leading">
                <Checkbox aria-label="选择内容块用于局部改写" checked={selectedBlocks.includes(block._key)} onCheckedChange={(checked) => setSelectedBlocks((current) => checked ? [...current, block._key] : current.filter((id) => id !== block._key))} />
                <Badge variant="outline">{blockLabels[block.block_type]}</Badge>
              </div>
              <div className="script-block-content">
                <div className="script-block-row">
                  <Select value={block.block_type} onValueChange={(value: ScriptBlockPayload["block_type"]) => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, blocks: item.blocks.map((candidate, candidateIndex) => candidateIndex === blockIndex ? { ...candidate, block_type: value } : candidate) } : item))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{Object.entries(blockLabels).map(([value, label]) => <SelectItem key={value} value={value}>{label}</SelectItem>)}</SelectContent></Select>
                  {block.block_type === "dialogue" ? (
                    <><Select value={block.character_snapshot_id ?? "temporary"} onValueChange={(value) => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, blocks: item.blocks.map((candidate, candidateIndex) => candidateIndex === blockIndex ? { ...candidate, character_snapshot_id: value === "temporary" ? undefined : value } : candidate) } : item))}><SelectTrigger><SelectValue placeholder="选择说话人" /></SelectTrigger><SelectContent><SelectItem value="temporary">临时人物</SelectItem>{workbench.characterSnapshots.map((character) => <SelectItem key={character.id} value={character.id}>{character.name}</SelectItem>)}</SelectContent></Select>{!block.character_snapshot_id ? <Input value={block.temporary_speaker_name ?? ""} maxLength={120} placeholder="临时人物名称" onChange={(event) => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, blocks: item.blocks.map((candidate, candidateIndex) => candidateIndex === blockIndex ? { ...candidate, temporary_speaker_name: event.target.value } : candidate) } : item))} /> : null}</>
                  ) : null}
                  <Input value={block.emotion ?? ""} maxLength={120} placeholder="情绪（可选）" onChange={(event) => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, blocks: item.blocks.map((candidate, candidateIndex) => candidateIndex === blockIndex ? { ...candidate, emotion: event.target.value } : candidate) } : item))} />
                </div>
                <Textarea value={block.content ?? ""} maxLength={10000} rows={2} placeholder={`${blockLabels[block.block_type]}内容`} onChange={(event) => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, blocks: item.blocks.map((candidate, candidateIndex) => candidateIndex === blockIndex ? { ...candidate, content: event.target.value } : candidate) } : item))} />
                <Input value={block.performance_note ?? ""} maxLength={1000} placeholder="表演、语气、停顿或动作提示（可选）" onChange={(event) => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, blocks: item.blocks.map((candidate, candidateIndex) => candidateIndex === blockIndex ? { ...candidate, performance_note: event.target.value } : candidate) } : item))} />
              </div>
              <div className="script-block-tools">
                <Button type="button" size="icon-sm" variant="ghost" aria-label="上移内容块" disabled={blockIndex === 0} onClick={() => mutateScenes((current) => current.map((item, index) => { if (index !== sceneIndex) return item; const blocks = [...item.blocks]; [blocks[blockIndex - 1], blocks[blockIndex]] = [blocks[blockIndex], blocks[blockIndex - 1]]; return { ...item, blocks }; }))}><ArrowUpIcon /></Button>
                <Button type="button" size="icon-sm" variant="ghost" aria-label="下移内容块" disabled={blockIndex === scene.blocks.length - 1} onClick={() => mutateScenes((current) => current.map((item, index) => { if (index !== sceneIndex) return item; const blocks = [...item.blocks]; [blocks[blockIndex + 1], blocks[blockIndex]] = [blocks[blockIndex], blocks[blockIndex + 1]]; return { ...item, blocks }; }))}><ArrowDownIcon /></Button>
                <Button type="button" size="icon-sm" variant="ghost" aria-label="删除内容块" onClick={() => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, blocks: item.blocks.filter((_, candidateIndex) => candidateIndex !== blockIndex) } : item))}><Trash2Icon /></Button>
              </div>
            </div>
          ))}
        </div>
        <div className="script-scene-footer">
          <Button type="button" variant="secondary" size="sm" onClick={() => mutateScenes((current) => current.map((item, index) => index === sceneIndex ? { ...item, blocks: [...item.blocks, emptyBlock()] } : item))}><PlusIcon data-icon="inline-start" />内容块</Button>
          {selectedBlocks.length ? <Button type="button" variant="secondary" size="sm" onClick={onRewriteBlocks} disabled={!canRewriteBlocks}><SparklesIcon data-icon="inline-start" />改写已选 {selectedBlocks.length} 块</Button> : null}
        </div>
      </div>
    </article>
  );
}

function ScriptSupportDrawer({
  open,
  onOpenChange,
  activeTab,
  onTabChange,
  projectId,
  episodeNo,
  content,
  issues,
  generations,
  onOpenGeneration
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  activeTab: SupportTab;
  onTabChange: (tab: SupportTab) => void;
  projectId: string;
  episodeNo: number;
  content: ProjectWorkbenchState["episodeContent"];
  issues: ScriptCheckIssue[];
  generations: ScriptGeneration[];
  onOpenGeneration: (generation: ScriptGeneration) => void;
}) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="structured-script-support-sheet sm:max-w-lg">
        <SheetHeader><SheetTitle>参考与检查</SheetTitle><SheetDescription>查看当前集来源正文、剧本问题和候选记录。</SheetDescription></SheetHeader>
        <Tabs value={activeTab} onValueChange={(value) => onTabChange(value as SupportTab)} className="script-support-tabs">
          <TabsList className="w-full"><TabsTrigger value="source">来源正文</TabsTrigger><TabsTrigger value="issues">结构检查 {issues.length ? `(${issues.length})` : ""}</TabsTrigger><TabsTrigger value="history">候选历史</TabsTrigger></TabsList>
          <TabsContent value="source"><SourceContentReference projectId={projectId} episodeNo={episodeNo} content={content} /></TabsContent>
          <TabsContent value="issues">
            {issues.length ? <div className="script-issue-list">{issues.map((issue, index) => <div className={`script-issue script-issue-${issue.severity}`} key={`${issue.code}-${index}`}><strong>{issue.severity === "error" ? "错误" : issue.severity === "warning" ? "警告" : "建议"}</strong><span>{issue.message}</span></div>)}</div> : <p className="hint">保存后运行检查，查看结构和语义风险。</p>}
          </TabsContent>
          <TabsContent value="history">
            {generations.length ? <div className="script-generation-list">{generations.slice(0, 20).map((generation) => <button type="button" key={generation.id} onClick={() => onOpenGeneration(generation)}><span>{generation.generation_scope === "episode" ? "整集" : generation.generation_scope === "scene" ? "场次" : "局部"}</span><small>{generation.status === "candidate" ? "待处理" : generation.status === "adopted" ? "已采用" : "已放弃"} · {new Date(generation.created_at).toLocaleString("zh-CN")}</small></button>)}</div> : <p className="hint">尚无候选记录。</p>}
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
}

function SourceContentReference({
  projectId,
  episodeNo,
  content
}: {
  projectId: string;
  episodeNo: number;
  content: ProjectWorkbenchState["episodeContent"];
}) {
  const detailedContent = content?.detailed_content?.trim() ?? "";
  const editHref = `/projects/${projectId}/story-text?stage=content&episode=${episodeNo}`;

  return (
    <section className="script-source-reference" aria-labelledby="script-source-title">
      <div className="inspector-heading">
        <div className="script-source-heading"><BookOpenIcon /><h3 id="script-source-title">来源正文</h3></div>
        {content ? <ArtifactStatusBadge status={content.status} /> : <Badge variant="outline">未创建</Badge>}
      </div>

        <div className="script-source-body">
          <div className="script-source-meta">
            <strong>第 {episodeNo} 集 · {content?.title?.trim() || "未命名正文"}</strong>
            <span>{content ? `${content.word_count} 字` : "暂无正文"}</span>
          </div>
          {detailedContent ? (
            <div className="script-source-content" tabIndex={0} aria-label={`第 ${episodeNo} 集故事正文`}>
              {detailedContent}
            </div>
          ) : (
            <div className="script-source-empty">
              <p>当前集还没有可供对照的故事正文。</p>
              <span>先完成正文后，才能生成完整的结构化剧本。</span>
            </div>
          )}
          <Button type="button" variant="secondary" size="sm" asChild>
            <Link href={editHref}>{detailedContent ? "前往编辑正文" : "前往创建正文"}</Link>
          </Button>
        </div>
    </section>
  );
}

function CandidatePreview({ generation }: { generation: ScriptGeneration }) {
  const output = generation.output_snapshot as { title?: string; scenes?: ScriptScenePayload[]; scene?: ScriptScenePayload; blocks?: ScriptBlockPayload[] };
  const scenes = output.scenes ?? (output.scene ? [output.scene] : []);
  if (generation.generation_scope === "blocks") {
    return <div className="candidate-blocks">{(output.blocks ?? []).map((block, index) => <div key={index}><Badge variant="outline">{blockLabels[block.block_type]}</Badge><p>{block.content || "空内容"}</p></div>)}</div>;
  }
  return <div className="candidate-scenes">{output.title ? <h3>{output.title}</h3> : null}{scenes.map((scene, index) => <section key={index}><h4>S{String(index + 1).padStart(2, "0")} · {scene.title || scene.location || "未命名场次"}</h4><p className="hint">{scene.location || "未填写地点"} · {scene.time_of_day ? timeLabels[scene.time_of_day] : "未填写时间"} · {scene.interior_exterior ? interiorLabels[scene.interior_exterior] : "未填写内外景"}</p>{scene.blocks.map((block, blockIndex) => <div key={blockIndex}><Badge variant="outline">{blockLabels[block.block_type]}</Badge><p>{block.content || "空内容"}</p></div>)}</section>)}</div>;
}
