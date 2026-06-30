"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Check, ChevronDown, ChevronRight, Copy, ExternalLink, List, Menu, Play, Plus, RefreshCw, Save, Trash2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
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
  reorderProjectStoryboardScene, updateProjectStoryboardShot
} from "@/lib/api";
import type { ModelConfig, ProjectStoryboard, ProjectStoryboardShot, ProjectStoryboardShotPayload, ShotVideoGeneration, StoryboardSceneGroup } from "@/lib/api";
import type { ProjectWorkbenchState } from "../_hooks/useProjectWorkbench";
import type { Stage } from "../_utils/workbenchTypes";
import { EpisodePicker } from "./shared";

type SwitchTarget = { kind: "shot"; id: string } | { kind: "episode"; episodeNo: number } | { kind: "stage"; stage: Stage };
type ShotStatus = ProjectStoryboardShot["status"];

const statusLabels: Record<ShotStatus, string> = {
  draft: "草稿", pending_review: "待审核", confirmed: "已确认", needs_review: "需检查"
};

function payloadFromShot(shot: ProjectStoryboardShot): ProjectStoryboardShotPayload {
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
    prompt: { ...shot.prompt, reference_asset_ids: shot.prompt?.reference_asset_ids ?? [] }
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
      image_prompt: clean(payload.prompt?.image_prompt), video_prompt: clean(payload.prompt?.video_prompt),
      negative_prompt: clean(payload.prompt?.negative_prompt), seedance_prompt: clean(payload.prompt?.seedance_prompt),
      first_frame_description: clean(payload.prompt?.first_frame_description),
      last_frame_description: clean(payload.prompt?.last_frame_description),
      aspect_ratio: clean(payload.prompt?.aspect_ratio),
      reference_asset_ids: payload.prompt?.reference_asset_ids ?? []
    }
  };
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
      await load(moved.id); setMessage(`${moved.display_code} 已重新归属`);
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
      const created = await createShotVideoGeneration(workbench.projectId, workbench.selectedEpisodeNo, selectedShot.id);
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

  const navigator = <ShotNavigator groups={groups} selectedId={selectedId} query={query} filter={filter} collapsed={collapsed} generationStates={generationStates}
    onQuery={setQuery} onFilter={setFilter} onToggle={(key) => setCollapsed((current) => { const next = new Set(current); next.has(key) ? next.delete(key) : next.add(key); return next; })}
    onSelect={(id) => requestSwitch({ kind: "shot", id })} onMove={move} onGenerate={(sceneId) => void generateScene(sceneId).then((ok) => ok ? load() : undefined)} />;

  return (
    <section className="overflow-hidden rounded-xl border bg-background shadow-sm">
      <header className="flex min-h-16 flex-wrap items-center gap-3 border-b bg-background/95 px-4 py-2 backdrop-blur">
        <Button className="xl:hidden" size="icon" variant="outline" onClick={() => setNavOpen(true)} aria-label="打开镜头导航"><Menu /></Button>
        <EpisodePicker episodeCount={workbench.project?.episode_count ?? 1} value={workbench.selectedEpisodeNo} onChange={(episodeNo) => requestSwitch({ kind: "episode", episodeNo })} />
        <div className="h-7 w-px bg-border" />
        <Metric label="来源" value={storyboard?.source_script_version ? `剧本 v${storyboard.source_script_version}` : "未关联"} />
        <Metric label="状态" value={storyboard ? statusLabels[storyboard.status] : "未创建"} />
        <Metric label="镜头" value={`${allShots.length}`} />
        <Metric label="总时长" value={`${(storyboard?.total_duration_seconds ?? 0).toFixed(1)}s`} />
        <div className="ml-auto flex gap-2">
          <Button variant="outline" onClick={() => void generateEpisode()} disabled={Object.values(generationStates).includes("running")}>生成整集分镜</Button>
          <Button onClick={() => void addShot()} disabled={saving || groups.length === 0}><Plus />新增镜头</Button>
        </div>
      </header>
      {(error || message) && <div className={`border-b px-4 py-2 text-sm ${error ? "bg-destructive/5 text-destructive" : "bg-emerald-50 text-emerald-700"}`}>{error || message}</div>}

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
                  <TabsContent value="visual" className="pt-5"><VisualForm draft={draft} update={update} /></TabsContent>
                  <TabsContent value="sound" className="pt-5"><SoundForm draft={draft} update={update} /></TabsContent>
                  <TabsContent value="prompt" className="pt-5"><PromptForm draft={draft} update={updatePrompt} /></TabsContent>
                  <TabsContent value="video" className="pt-5"><VideoGenerationPanel shot={selectedShot} draft={draft} generations={videoGenerations} videoConfigs={videoConfigs} loading={videoLoading} busy={videoBusy} isDirty={isDirty} onCreate={() => void createVideo()} onRefresh={(id) => void refreshVideo(id)} onAdopt={(id) => void adoptVideo(id)} onCancel={(id) => void cancelVideo(id)} /></TabsContent>
                  <TabsContent value="reference" className="pt-5"><ReferencePanel shot={selectedShot} groups={groups} script={workbench.episodeScript} onReassign={(sceneId) => void reassign(sceneId)} disabled={saving || isDirty} /></TabsContent>
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

function Field({ label, value, onChange, placeholder }: { label: string; value?: string; onChange: (value: string) => void; placeholder?: string }) { return <label className="space-y-1.5 text-sm"><span className="font-medium">{label}</span><Input value={value ?? ""} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} /></label>; }
function Area({ label, value, onChange, rows = 4 }: { label: string; value?: string; onChange: (value: string) => void; rows?: number }) { return <label className="space-y-1.5 text-sm"><span className="font-medium">{label}</span><Textarea rows={rows} value={value ?? ""} onChange={(event) => onChange(event.target.value)} /></label>; }

function VisualForm({ draft, update }: { draft: ProjectStoryboardShotPayload; update: (field: keyof ProjectStoryboardShotPayload, value: unknown) => void }) { return <div className="grid gap-4 md:grid-cols-2">
  <Field label="景别" value={draft.shot_size} onChange={(value) => update("shot_size", value)} placeholder="特写 / 中景 / 全景" />
  <label className="space-y-1.5 text-sm"><span className="font-medium">时长（秒）</span><Input type="number" min="0.1" step="0.1" value={draft.duration_seconds ?? ""} onChange={(event) => update("duration_seconds", Number(event.target.value))} /></label>
  <Area label="主体" value={draft.subject_description} onChange={(value) => update("subject_description", value)} />
  <Area label="核心画面" value={draft.visual_description} onChange={(value) => update("visual_description", value)} />
  <Area label="动作" value={draft.action} onChange={(value) => update("action", value)} />
  <Area label="连续性备注" value={draft.continuity_note} onChange={(value) => update("continuity_note", value)} />
  <Field label="机位 / 角度" value={draft.camera_angle} onChange={(value) => update("camera_angle", value)} />
  <Field label="运镜" value={draft.camera_movement} onChange={(value) => update("camera_movement", value)} />
  <Area label="构图" value={draft.composition} onChange={(value) => update("composition", value)} rows={3} />
  <Area label="环境" value={draft.environment} onChange={(value) => update("environment", value)} rows={3} />
</div>; }

function SoundForm({ draft, update }: { draft: ProjectStoryboardShotPayload; update: (field: keyof ProjectStoryboardShotPayload, value: unknown) => void }) { return <div className="grid gap-4 md:grid-cols-2">
  <Area label="对白" value={draft.dialogue_snapshot} onChange={(value) => update("dialogue_snapshot", value)} />
  <Area label="旁白" value={draft.voiceover_snapshot} onChange={(value) => update("voiceover_snapshot", value)} />
  <Area label="音效" value={draft.sound_effect} onChange={(value) => update("sound_effect", value)} />
  <Area label="音乐" value={draft.music_note} onChange={(value) => update("music_note", value)} />
</div>; }

function PromptForm({ draft, update }: { draft: ProjectStoryboardShotPayload; update: (field: string, value: string) => void }) { return <div className="grid gap-4 md:grid-cols-2">
  <Area label="图片提示词" value={draft.prompt?.image_prompt} onChange={(value) => update("image_prompt", value)} />
  <Area label="视频提示词" value={draft.prompt?.video_prompt} onChange={(value) => update("video_prompt", value)} />
  <Area label="负面词" value={draft.prompt?.negative_prompt} onChange={(value) => update("negative_prompt", value)} />
  <Area label="Seedance 提示词" value={draft.prompt?.seedance_prompt} onChange={(value) => update("seedance_prompt", value)} />
  <Field label="首帧描述" value={draft.prompt?.first_frame_description} onChange={(value) => update("first_frame_description", value)} />
  <Field label="尾帧描述" value={draft.prompt?.last_frame_description} onChange={(value) => update("last_frame_description", value)} />
</div>; }

const videoStatusLabels: Record<ShotVideoGeneration["status"], string> = {
  queued: "排队中", running: "生成中", succeeded: "成功", failed: "失败", canceled: "已取消"
};

function VideoGenerationPanel({ shot, draft, generations, videoConfigs, loading, busy, isDirty, onCreate, onRefresh, onAdopt, onCancel }: {
  shot: ProjectStoryboardShot; draft: ProjectStoryboardShotPayload; generations: ShotVideoGeneration[]; videoConfigs: ModelConfig[];
  loading: boolean; busy: boolean; isDirty: boolean; onCreate: () => void; onRefresh: (id: string) => void; onAdopt: (id: string) => void; onCancel: (id: string) => void;
}) {
  const promptText = draft.prompt?.seedance_prompt?.trim() || draft.prompt?.video_prompt?.trim() || "";
  const enabledVideoConfig = videoConfigs.find((config) => config.enabled);
  const adopted = generations.find((item) => item.adopted);
  const disabledReason = isDirty ? "请先保存当前镜头修改后再生成视频。"
    : !promptText ? "请先填写 Seedance 提示词或视频提示词。"
      : shot.prompt_freshness === "needs_update" ? "提示词需要更新，请先保存或确认后再生成视频。"
        : !enabledVideoConfig ? "请先在设置中启用视频生成模型。"
          : enabledVideoConfig.last_test_status !== "success" ? "请先测试并通过当前视频生成模型。"
            : "";
  return <div className="space-y-4">
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]">
      <div className="rounded-lg border p-4">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="font-semibold">本次使用提示词</h3>
          <Badge variant="secondary">{draft.prompt?.seedance_prompt?.trim() ? "Seedance" : "通用视频"}</Badge>
          {shot.prompt_freshness === "needs_update" ? <Badge variant="outline">需更新</Badge> : null}
        </div>
        <p className="mt-3 whitespace-pre-wrap rounded-md bg-muted/60 p-3 text-sm text-muted-foreground">{promptText || "暂无可用视频提示词。"}</p>
      </div>
      <div className="rounded-lg border p-4">
        <h3 className="font-semibold">视频模型</h3>
        <p className="mt-2 text-sm">{enabledVideoConfig ? enabledVideoConfig.provider_name : "未启用"}</p>
        <p className="mt-1 text-xs text-muted-foreground">{enabledVideoConfig ? `${enabledVideoConfig.model_name} · ${enabledVideoConfig.last_test_status}` : "请先到设置页配置视频模型。"}</p>
        {disabledReason ? <p className="mt-3 text-sm text-destructive">{disabledReason}</p> : null}
        <Button className="mt-4 w-full" onClick={onCreate} disabled={busy || Boolean(disabledReason)}><Play />{busy ? "处理中" : "生成视频"}</Button>
      </div>
    </div>
    {adopted ? <VideoResultCard generation={adopted} title="当前采用素材" busy={busy} onRefresh={onRefresh} onAdopt={onAdopt} onCancel={onCancel} /> : <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">当前镜头还没有采用的视频素材。</div>}
    <div className="rounded-lg border">
      <div className="flex items-center justify-between border-b px-4 py-3"><h3 className="font-semibold">候选历史</h3>{loading ? <span className="text-xs text-muted-foreground">加载中...</span> : null}</div>
      <div className="divide-y">{generations.length === 0 && !loading ? <p className="p-4 text-sm text-muted-foreground">暂无视频生成记录。</p> : generations.map((generation) => <VideoResultCard key={generation.id} generation={generation} busy={busy} onRefresh={onRefresh} onAdopt={onAdopt} onCancel={onCancel} />)}</div>
    </div>
  </div>;
}

function VideoResultCard({ generation, title, busy, onRefresh, onAdopt, onCancel }: {
  generation: ShotVideoGeneration; title?: string; busy: boolean; onRefresh: (id: string) => void; onAdopt: (id: string) => void; onCancel: (id: string) => void;
}) {
  const canPreview = generation.result_url || generation.local_asset_path;
  return <div className="grid gap-4 p-4 lg:grid-cols-[220px_minmax(0,1fr)]">
    <div className="flex aspect-video items-center justify-center overflow-hidden rounded-md bg-muted">
      {generation.result_url ? <video className="h-full w-full object-cover" src={generation.result_url} controls poster={generation.thumbnail_url} /> : generation.thumbnail_url ? <img className="h-full w-full object-cover" src={generation.thumbnail_url} alt="视频缩略图" /> : <span className="text-xs text-muted-foreground">暂无预览</span>}
    </div>
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
        {(generation.status === "queued" || generation.status === "running") ? <Button size="sm" variant="outline" onClick={() => onRefresh(generation.id)} disabled={busy}><RefreshCw />刷新</Button> : null}
        {(generation.status === "queued" || generation.status === "running") ? <Button size="sm" variant="outline" onClick={() => onCancel(generation.id)} disabled={busy}><X />取消</Button> : null}
        {generation.status === "failed" ? <Button size="sm" variant="outline" onClick={() => onRefresh(generation.id)} disabled={busy}><RefreshCw />重试刷新</Button> : null}
        {generation.status === "succeeded" && !generation.adopted ? <Button size="sm" onClick={() => onAdopt(generation.id)} disabled={busy || !canPreview}><Check />采用</Button> : null}
        {generation.result_url ? <Button asChild size="sm" variant="outline"><a href={generation.result_url} target="_blank" rel="noreferrer"><ExternalLink />打开</a></Button> : null}
      </div>
    </div>
  </div>;
}

function ReferencePanel({ shot, groups, script, onReassign, disabled }: { shot: ProjectStoryboardShot; groups: StoryboardSceneGroup[]; script: ProjectWorkbenchState["episodeScript"]; onReassign: (sceneId: string) => void; disabled: boolean }) {
  const group = groups.find((item) => item.scene_id === shot.source_scene_id);
  const scene = script?.scenes.find((item) => item.id === shot.source_scene_id);
  return <div className="grid gap-4 lg:grid-cols-2">
    <div className="rounded-lg border p-4"><h3 className="font-semibold">来源剧本块 · {group?.display_code ?? "未归属"}</h3><p className="mt-1 text-sm text-muted-foreground">{group?.title}</p><div className="mt-4 space-y-2">{scene?.blocks.map((block) => <p key={block.id} className="rounded-md bg-muted/60 p-2 text-sm"><span className="mr-2 text-xs text-muted-foreground">{block.block_type}</span>{block.content || "（空）"}</p>) ?? <p className="text-sm text-muted-foreground">暂无来源剧本块。</p>}</div></div>
    <div className="space-y-3"><div className="rounded-lg border p-4"><h3 className="font-semibold">连续性与检查</h3><p className="mt-2 text-sm text-muted-foreground">来源状态：{shot.source_status}；提示词状态：{shot.prompt_freshness}</p>{shot.status === "needs_review" && <p className="mt-2 text-sm text-destructive">该镜头需要人工检查后再确认。</p>}<div className="mt-4"><p className="mb-1.5 text-sm font-medium">重新归属场次</p><Select value={shot.source_scene_id ?? ""} onValueChange={onReassign} disabled={disabled}><SelectTrigger className="w-full"><SelectValue placeholder="选择场次" /></SelectTrigger><SelectContent>{groups.filter((item) => item.scene_id).map((item) => <SelectItem key={item.scene_id} value={item.scene_id!}>{item.display_code} · {item.title}</SelectItem>)}</SelectContent></Select>{disabled && <p className="mt-1 text-xs text-muted-foreground">请先保存当前修改。</p>}</div></div><div className="rounded-lg border p-4"><h3 className="font-semibold">人物素材</h3><p className="mt-2 text-sm text-muted-foreground">已关联 {shot.character_snapshot_ids?.length ?? 0} 个人物快照。</p></div></div>
  </div>;
}

function ContinuityStrip({ shots, selectedId, groups, onSelect }: { shots: ProjectStoryboardShot[]; selectedId: string; groups: StoryboardSceneGroup[]; onSelect: (id: string) => void }) { return <div className="border-t bg-muted/30 p-3"><div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground"><List className="size-3.5" />连续性 · 前后各 2 镜</div><div className="grid grid-cols-5 gap-2">{shots.map((shot) => { const group = groups.find((item) => item.scene_id === shot.source_scene_id); return <button key={shot.id} onClick={() => onSelect(shot.id)} className={`min-w-0 rounded-lg border p-2 text-left ${shot.id === selectedId ? "border-primary bg-background shadow-sm" : "bg-background/60 hover:bg-background"}`}><div className="flex items-center gap-1"><strong className="text-xs">{shot.display_code}</strong><span className="truncate text-[10px] text-muted-foreground">{group?.display_code}</span></div><p className="mt-1 truncate text-xs text-muted-foreground">{shot.subject_description || shot.action || "未填写摘要"}</p></button>; })}</div></div>; }

function EmptyState({ hasScenes, onAdd }: { hasScenes: boolean; onAdd: () => void }) { return <div className="flex h-full flex-col items-center justify-center gap-3 text-center"><div className="rounded-full bg-muted p-3"><List className="size-5" /></div><div><h2 className="font-semibold">当前集还没有镜头</h2><p className="mt-1 text-sm text-muted-foreground">{hasScenes ? "从首个场次创建镜头并开始逐镜精修。" : "请先完成结构化剧本场次。"}</p></div>{hasScenes && <Button onClick={onAdd}><Plus />新增镜头</Button>}</div>; }
