"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  adoptProjectEpisodeContentGeneration,
  createProjectStoryboardShot,
  deleteProjectCharacterSnapshot,
  deleteProjectStoryboardShot,
  deleteProjectWorldSnapshot,
  discardProjectEpisodeContentGeneration,
  generateProjectEpisodeContent,
  getProject,
  getProjectCopywriting,
  getProjectEpisodeContent,
  getProjectEpisodeScript,
  getProjectStoryOutline,
  listCharacterCards,
  listProjectCharacterSnapshots,
  listProjectEpisodeOutlines,
  listProjectEpisodeContentGenerations,
  listProjectStoryboardShots,
  listProjectWorldSnapshots,
  listWorldBooks,
  loadCharacterCardToProject,
  loadWorldBookToProject,
  updateProject,
  updateProjectCharacterSnapshot,
  updateProjectCopywriting,
  updateProjectEpisodeContent,
  updateProjectEpisodeContentGeneration,
  updateProjectEpisodeOutline,
  updateProjectEpisodeScript,
  updateProjectStoryboardShot,
  updateProjectStoryOutline,
  updateProjectWorldSnapshot
} from "@/lib/api";
import type {
  CharacterCard,
  EpisodeContentGeneration,
  EpisodeContentGenerationType,
  ProjectCharacterSnapshot,
  ProjectCopywriting,
  ProjectEpisodeContent,
  ProjectEpisodeOutline,
  ProjectEpisodeScript,
  ProjectStoryboardShot,
  ProjectStoryOutline,
  ProjectSummary,
  ProjectWorldSnapshot,
  WorldBook
} from "@/lib/api";
import {
  copywritingToForm,
  countContentCharacters,
  defaultStageForMode,
  emptyCharacterSnapshotForm,
  emptyContentForm,
  emptyCopyForm,
  emptyEpisodeForm,
  emptyProjectForm,
  emptyScriptForm,
  emptyShotForm,
  emptyStoryForm,
  emptyWorldSnapshotForm,
  episodeContentToForm,
  episodeOutlineToForm,
  episodeScriptToForm,
  characterSnapshotFormToPayload,
  nextShotNo,
  projectToForm,
  replaceCharacterSnapshot,
  replaceEpisodeOutline,
  replaceShot,
  replaceWorldSnapshot,
  shotToForm,
  storyFormToPayload,
  storyOutlineToForm,
  toOptional,
  toOptionalNumber,
  validateProject,
  worldSnapshotFormToPayload,
  worldSnapshotToForm,
  characterSnapshotToForm
} from "../_utils/workbenchForms";
import type {
  CharacterSnapshotForm,
  CopywritingForm,
  EpisodeContentForm,
  EpisodeOutlineForm,
  EpisodeScriptForm,
  ProjectForm,
  ReferenceTab,
  ShotForm,
  Stage,
  StoryOutlineForm,
  WorkspaceMode,
  WorldSnapshotForm
} from "../_utils/workbenchTypes";
import { workspaceGroups } from "../_utils/workbenchTypes";

type PendingConfirmation = {
  title: string;
  description: string;
  confirmLabel: string;
  destructive?: boolean;
  onConfirm: () => void | Promise<void>;
};

export function useProjectWorkbench({
  projectId,
  mode,
  requestedStage,
  requestedEpisodeNo
}: {
  projectId: string;
  mode: WorkspaceMode;
  requestedStage: string | null;
  requestedEpisodeNo: number | null;
}) {
  const isLandingMode = mode === "landing";
  const visibleGroups = useMemo(
    () => (isLandingMode ? workspaceGroups : workspaceGroups.filter((group) => group.key === mode)),
    [isLandingMode, mode]
  );
  const visibleStages = useMemo(() => visibleGroups.flatMap((group) => group.stages), [visibleGroups]);
  const normalizedRequestedStage = requestedStage === "assets" ? "world" : requestedStage;
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [activeStage, setActiveStage] = useState<Stage>(() => defaultStageForMode(mode));
  const [selectedEpisodeNo, setSelectedEpisodeNo] = useState(requestedEpisodeNo ?? 1);

  const [worldSnapshots, setWorldSnapshots] = useState<ProjectWorldSnapshot[]>([]);
  const [characterSnapshots, setCharacterSnapshots] = useState<ProjectCharacterSnapshot[]>([]);
  const [storyOutline, setStoryOutline] = useState<ProjectStoryOutline | null>(null);
  const [episodeOutlines, setEpisodeOutlines] = useState<ProjectEpisodeOutline[]>([]);
  const [episodeContent, setEpisodeContent] = useState<ProjectEpisodeContent | null>(null);
  const [previousEpisodeContent, setPreviousEpisodeContent] = useState<ProjectEpisodeContent | null>(null);
  const [episodeScript, setEpisodeScript] = useState<ProjectEpisodeScript | null>(null);
  const [storyboardShots, setStoryboardShots] = useState<ProjectStoryboardShot[]>([]);
  const [copywriting, setCopywriting] = useState<ProjectCopywriting | null>(null);
  const [episodeContentGenerations, setEpisodeContentGenerations] = useState<EpisodeContentGeneration[]>([]);
  const [activeContentGenerationId, setActiveContentGenerationId] = useState("");
  const [contentGenerationType, setContentGenerationType] = useState<EpisodeContentGenerationType>("create");
  const [contentGenerationInstruction, setContentGenerationInstruction] = useState("");
  const [contentGenerationDraft, setContentGenerationDraft] = useState("");
  const [contentEditorMode, setContentEditorMode] = useState<"current" | "candidate">("current");
  const [showContentCreator, setShowContentCreator] = useState(false);

  const [projectForm, setProjectForm] = useState<ProjectForm>(emptyProjectForm);
  const [storyForm, setStoryForm] = useState<StoryOutlineForm>(emptyStoryForm);
  const [episodeForm, setEpisodeForm] = useState<EpisodeOutlineForm>(emptyEpisodeForm);
  const [contentForm, setContentForm] = useState<EpisodeContentForm>(emptyContentForm);
  const [scriptForm, setScriptForm] = useState<EpisodeScriptForm>(emptyScriptForm);
  const [shotForm, setShotForm] = useState<ShotForm>(emptyShotForm);
  const [editingShotId, setEditingShotId] = useState("");
  const [copyForm, setCopyForm] = useState<CopywritingForm>(emptyCopyForm);
  const [worldSnapshotForm, setWorldSnapshotForm] = useState<WorldSnapshotForm>(emptyWorldSnapshotForm);
  const [editingWorldSnapshotId, setEditingWorldSnapshotId] = useState("");
  const [characterSnapshotForm, setCharacterSnapshotForm] = useState<CharacterSnapshotForm>(emptyCharacterSnapshotForm);
  const [editingCharacterSnapshotId, setEditingCharacterSnapshotId] = useState("");

  const [error, setError] = useState("");
  const [assetError, setAssetError] = useState("");
  const [artifactError, setArtifactError] = useState("");
  const [status, setStatus] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingAssets, setIsLoadingAssets] = useState(false);
  const [isLoadingEpisodeArtifacts, setIsLoadingEpisodeArtifacts] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isGeneratingContent, setIsGeneratingContent] = useState(false);
  const [isSavingContentGeneration, setIsSavingContentGeneration] = useState(false);
  const [isAdoptingContentGeneration, setIsAdoptingContentGeneration] = useState(false);
  const [savingSnapshotId, setSavingSnapshotId] = useState("");
  const [removingSnapshotId, setRemovingSnapshotId] = useState("");
  const [removingShotId, setRemovingShotId] = useState("");
  const [pendingConfirmation, setPendingConfirmation] = useState<PendingConfirmation | null>(null);

  const [showWorldPicker, setShowWorldPicker] = useState(false);
  const [showCharacterPicker, setShowCharacterPicker] = useState(false);
  const [availableWorlds, setAvailableWorlds] = useState<WorldBook[]>([]);
  const [availableCharacters, setAvailableCharacters] = useState<CharacterCard[]>([]);
  const [isLoadingPicker, setIsLoadingPicker] = useState(false);
  const [loadingAssetId, setLoadingAssetId] = useState("");
  const [selectedWorldId, setSelectedWorldId] = useState<string | null>(null);
  const [selectedCharacterIds, setSelectedCharacterIds] = useState<Set<string>>(new Set());
  const [isBatchLoading, setIsBatchLoading] = useState(false);
  const [activeReferenceTab, setActiveReferenceTab] = useState<ReferenceTab>("settings");

  const episodeCount = Number(projectForm.episode_count);
  const episodeDuration = Number(projectForm.episode_duration);
  const totalDuration = useMemo(() => episodeCount * episodeDuration, [episodeCount, episodeDuration]);
  const loadedWorldIds = useMemo(() => new Set(worldSnapshots.map((s) => s.source_world_book_id)), [worldSnapshots]);
  const loadedCharacterIds = useMemo(() => new Set(characterSnapshots.map((s) => s.source_character_card_id)), [characterSnapshots]);
  const validationError = validateProject(projectForm, episodeCount, episodeDuration, totalDuration);
  const durationChanged =
    Boolean(project) &&
    (project?.episode_count !== episodeCount || project?.episode_duration !== episodeDuration);

  const episodeRows = useMemo(() => {
    const count = Math.max(project?.episode_count ?? 0, 0);
    return Array.from({ length: count }, (_, index) => {
      const episodeNo = index + 1;
      return {
        episodeNo,
        outline: episodeOutlines.find((outline) => outline.episode_no === episodeNo) ?? null
      };
    });
  }, [episodeOutlines, project?.episode_count]);
  const selectedEpisodeOutline = useMemo(
    () => episodeOutlines.find((outline) => outline.episode_no === selectedEpisodeNo) ?? null,
    [episodeOutlines, selectedEpisodeNo]
  );
  const activeContentGeneration = useMemo(
    () => episodeContentGenerations.find((item) => item.id === activeContentGenerationId) ?? null,
    [activeContentGenerationId, episodeContentGenerations]
  );
  const canGenerateEpisodeContent = Boolean(
    selectedEpisodeOutline &&
      (selectedEpisodeOutline.title ||
        selectedEpisodeOutline.synopsis ||
        selectedEpisodeOutline.hook ||
        selectedEpisodeOutline.conflict ||
        selectedEpisodeOutline.reversal ||
        selectedEpisodeOutline.cliffhanger)
  );
  const hasSavedEpisodeContent = Boolean(episodeContent?.detailed_content?.trim());
  const canContinueEpisodeContent = hasSavedEpisodeContent;
  const canPolishEpisodeContent = hasSavedEpisodeContent;
  const activeWorkspaceGroup =
    workspaceGroups.find((group) => group.stages.some((stage) => stage.key === activeStage)) ?? workspaceGroups[0];
  const currentWorkspaceGroup = isLandingMode ? null : workspaceGroups.find((group) => group.key === mode) ?? activeWorkspaceGroup;
  const filledEpisodeOutlineCount = useMemo(
    () => episodeOutlines.filter((outline) => Boolean(outline.title || outline.synopsis)).length,
    [episodeOutlines]
  );
  const storyOutlineStatus = storyOutline?.status ?? storyForm.status;
  const episodeContentStatus = episodeContent?.status ?? contentForm.status;
  const episodeScriptStatus = episodeScript?.status ?? "draft";
  const copywritingStatus = copywriting?.status ?? copyForm.status;
  const contentWordCount = useMemo(() => countContentCharacters(contentForm.detailed_content), [contentForm.detailed_content]);
  const previousEpisodeSummary =
    selectedEpisodeNo <= 1
      ? "第 1 集暂无前文参考。"
      : previousEpisodeContent?.chapter_summary || `第 ${selectedEpisodeNo - 1} 集尚未填写正文摘要。`;

  useEffect(() => {
    void refreshWorkbench();
  }, [projectId]);

  useEffect(() => {
    if (normalizedRequestedStage && visibleStages.some((stage) => stage.key === normalizedRequestedStage)) {
      setActiveStage(normalizedRequestedStage as Stage);
      return;
    }
    if (!visibleStages.some((stage) => stage.key === activeStage)) {
      setActiveStage(defaultStageForMode(mode));
    }
  }, [activeStage, mode, normalizedRequestedStage, visibleStages]);

  useEffect(() => {
    if (!project) return;
    const nextEpisodeNo = Math.min(Math.max(selectedEpisodeNo, 1), Math.max(project.episode_count, 1));
    if (nextEpisodeNo !== selectedEpisodeNo) {
      setSelectedEpisodeNo(nextEpisodeNo);
      return;
    }
    void refreshEpisodeArtifacts(nextEpisodeNo);
  }, [project?.id, project?.episode_count, selectedEpisodeNo]);

  useEffect(() => {
    setEpisodeForm(episodeOutlineToForm(episodeOutlines.find((outline) => outline.episode_no === selectedEpisodeNo) ?? null));
  }, [episodeOutlines, selectedEpisodeNo]);

  const refreshWorkbench = async () => {
    setIsLoading(true);
    setError("");
    setAssetError("");
    setArtifactError("");
    setStatus("");
    try {
      const projectDetail = await getProject(projectId);
      setProject(projectDetail);
      setProjectForm(projectToForm(projectDetail));
      void refreshAssets();
      void refreshStoryAndEpisodes();
    } catch (err) {
      setError(err instanceof Error ? err.message : "项目工作台加载失败");
    } finally {
      setIsLoading(false);
    }
  };

  const refreshAssets = async () => {
    setIsLoadingAssets(true);
    setAssetError("");
    try {
      const [worlds, characters] = await Promise.all([
        listProjectWorldSnapshots(projectId),
        listProjectCharacterSnapshots(projectId)
      ]);
      setWorldSnapshots(worlds);
      setCharacterSnapshots(characters);
    } catch (err) {
      setAssetError(err instanceof Error ? err.message : "项目资产加载失败");
      setWorldSnapshots([]);
      setCharacterSnapshots([]);
    } finally {
      setIsLoadingAssets(false);
    }
  };

  const refreshStoryAndEpisodes = async () => {
    setArtifactError("");
    try {
      const [outline, outlines] = await Promise.all([
        getProjectStoryOutline(projectId),
        listProjectEpisodeOutlines(projectId)
      ]);
      setStoryOutline(outline);
      setStoryForm(storyOutlineToForm(outline));
      setEpisodeOutlines(outlines);
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "项目创作内容加载失败");
    }
  };

  const refreshEpisodeArtifacts = async (episodeNo: number) => {
    setIsLoadingEpisodeArtifacts(true);
    setArtifactError("");
    try {
      const [content, previousContent, script, shots, copy, generations] = await Promise.all([
        getProjectEpisodeContent(projectId, episodeNo),
        episodeNo > 1 ? getProjectEpisodeContent(projectId, episodeNo - 1) : Promise.resolve(null),
        getProjectEpisodeScript(projectId, episodeNo),
        listProjectStoryboardShots(projectId, episodeNo),
        getProjectCopywriting(projectId, episodeNo),
        listProjectEpisodeContentGenerations(projectId, episodeNo)
      ]);
      setEpisodeContent(content);
      setPreviousEpisodeContent(previousContent);
      setEpisodeScript(script);
      setStoryboardShots(shots);
      setCopywriting(copy);
      setEpisodeContentGenerations(generations);
      const recoverableCandidate = generations.find((item) => item.status === "candidate") ?? null;
      setActiveContentGenerationId(recoverableCandidate?.id ?? "");
      setContentGenerationType(recoverableCandidate?.generation_type ?? "create");
      setContentGenerationDraft(recoverableCandidate?.output_text ?? "");
      setContentGenerationInstruction(recoverableCandidate?.instruction ?? "");
      setContentEditorMode(recoverableCandidate ? "candidate" : "current");
      setShowContentCreator(Boolean(recoverableCandidate));
      setContentForm(episodeContentToForm(content));
      setScriptForm(episodeScriptToForm(script));
      setCopyForm(copywritingToForm(copy));
      resetShotForm(shots);
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "单集创作内容加载失败");
    } finally {
      setIsLoadingEpisodeArtifacts(false);
    }
  };

  const refreshDownstreamAfterAssetChange = () => {
    // 项目资产变化会影响故事文本和制作文本，只刷新下游产物，不重载当前编辑副本。
    void refreshStoryAndEpisodes();
    void refreshEpisodeArtifacts(selectedEpisodeNo);
  };

  const saveProject = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setStatus("");
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSaving(true);
    try {
      const updatedProject = await updateProject(projectId, {
        title: toOptional(projectForm.title),
        idea: projectForm.idea,
        target_platform: toOptional(projectForm.target_platform),
        genre: toOptional(projectForm.genre),
        episode_count: episodeCount,
        episode_duration: episodeDuration,
        target_audience: toOptional(projectForm.target_audience),
        style: toOptional(projectForm.style),
        remark: toOptional(projectForm.remark)
      });
      setProject(updatedProject);
      setProjectForm(projectToForm(updatedProject));
      setStatus("项目信息已保存，故事文本和短剧制作已有内容已标记为需要检查。");
      refreshDownstreamAfterAssetChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "项目信息保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const saveStoryOutline = async (event: FormEvent) => {
    event.preventDefault();
    setIsSaving(true);
    setArtifactError("");
    setStatus("");
    try {
      const saved = await updateProjectStoryOutline(projectId, storyFormToPayload(storyForm));
      setStoryOutline(saved);
      setStoryForm(storyOutlineToForm(saved));
      setStatus("整体故事大纲已保存，分集大纲、单集故事正文和短剧制作内容已标记为需要检查。");
      void refreshStoryAndEpisodes();
      void refreshEpisodeArtifacts(selectedEpisodeNo);
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "整体故事大纲保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const saveEpisodeOutline = async (event: FormEvent) => {
    event.preventDefault();
    setIsSaving(true);
    setArtifactError("");
    setStatus("");
    try {
      const saved = await updateProjectEpisodeOutline(projectId, selectedEpisodeNo, {
        title: toOptional(episodeForm.title),
        synopsis: toOptional(episodeForm.synopsis),
        hook: toOptional(episodeForm.hook),
        conflict: toOptional(episodeForm.conflict),
        reversal: toOptional(episodeForm.reversal),
        cliffhanger: toOptional(episodeForm.cliffhanger),
        duration_minutes: toOptionalNumber(episodeForm.duration_minutes),
        status: episodeForm.status
      });
      setEpisodeOutlines((current) => replaceEpisodeOutline(current, saved));
      setEpisodeForm(episodeOutlineToForm(saved));
      setStatus(`第 ${selectedEpisodeNo} 集分集大纲已保存，同集单集故事正文和短剧制作内容已标记为需要检查。`);
      void refreshEpisodeArtifacts(selectedEpisodeNo);
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "分集大纲保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const saveEpisodeContent = async (event: FormEvent) => {
    event.preventDefault();
    setIsSaving(true);
    setArtifactError("");
    setStatus("");
    try {
      const saved = await updateProjectEpisodeContent(projectId, selectedEpisodeNo, {
        title: toOptional(selectedEpisodeOutline?.title || contentForm.title),
        detailed_content: toOptional(contentForm.detailed_content),
        chapter_summary: toOptional(contentForm.chapter_summary),
        hook: toOptional(episodeContent?.hook || contentForm.hook),
        key_beats: toOptional(episodeContent?.key_beats || contentForm.key_beats),
        previous_context_summary: toOptional(episodeContent?.previous_context_summary || contentForm.previous_context_summary),
        quality_check_notes: toOptional(contentForm.quality_check_notes),
        status: contentForm.status
      });
      setEpisodeContent(saved);
      setContentForm(episodeContentToForm(saved));
      setStatus(`第 ${selectedEpisodeNo} 集单集故事正文已保存，同集短剧制作内容已标记为需要检查。`);
      void refreshEpisodeArtifacts(selectedEpisodeNo);
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "单集故事正文保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const createContentGenerationRequestId = () => {
    if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
    return `episode-content-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  };

  const openEpisodeContentCreator = (generationType: EpisodeContentGenerationType = "create") => {
    setArtifactError("");
    if (generationType === "create" && !canGenerateEpisodeContent) {
      setStatus("");
      setArtifactError("请先完善并保存本集分集大纲，再生成正文。");
      return;
    }
    if (generationType === "continue" && !canContinueEpisodeContent) {
      setStatus("");
      setArtifactError("续写需要当前正文非空，请先填写并保存正文。");
      return;
    }
    if (generationType === "polish" && !canPolishEpisodeContent) {
      setStatus("");
      setArtifactError("润色需要当前正文非空，请先填写并保存正文。");
      return;
    }
    setContentGenerationType(generationType);
    setShowContentCreator(true);
  };

  const generateEpisodeContentCandidate = async () => {
    if (isGeneratingContent) return;
    if (contentGenerationType === "create" && !canGenerateEpisodeContent) return;
    if (contentGenerationType === "continue" && !canContinueEpisodeContent) return;
    if (contentGenerationType === "polish" && !canPolishEpisodeContent) return;
    setIsGeneratingContent(true);
    setArtifactError("");
    setStatus("");
    try {
      const generated = await generateProjectEpisodeContent(projectId, selectedEpisodeNo, {
        instruction: toOptional(contentGenerationInstruction),
        client_request_id: createContentGenerationRequestId(),
        generation_type: contentGenerationType
      });
      setEpisodeContentGenerations((current) => [generated, ...current.filter((item) => item.id !== generated.id)].slice(0, 10));
      setActiveContentGenerationId(generated.id);
      setContentGenerationDraft(generated.output_text);
      setContentEditorMode("candidate");
      setShowContentCreator(true);
      setContentGenerationType(generated.generation_type);
      setStatus(`第 ${selectedEpisodeNo} 集${episodeContentGenerationTypeLabel(generated.generation_type)}候选稿已生成，采用前不会覆盖当前正文。`);
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "正文候选稿生成失败，请稍后重试");
    } finally {
      setIsGeneratingContent(false);
    }
  };

  const selectContentGeneration = (generationId: string) => {
    const generation = episodeContentGenerations.find((item) => item.id === generationId);
    if (!generation) return;
    setActiveContentGenerationId(generation.id);
    setContentGenerationType(generation.generation_type);
    setContentGenerationDraft(generation.output_text);
    setContentGenerationInstruction(generation.instruction ?? "");
    setContentEditorMode("candidate");
    setShowContentCreator(true);
  };

  const saveContentGenerationDraft = async () => {
    if (!activeContentGeneration || activeContentGeneration.status !== "candidate") return activeContentGeneration;
    if (!contentGenerationDraft.trim()) {
      setArtifactError("候选稿不能为空。");
      return null;
    }
    setIsSavingContentGeneration(true);
    setArtifactError("");
    try {
      const saved = await updateProjectEpisodeContentGeneration(
        projectId,
        selectedEpisodeNo,
        activeContentGeneration.id,
        contentGenerationDraft
      );
      setEpisodeContentGenerations((current) => current.map((item) => (item.id === saved.id ? saved : item)));
      setContentGenerationDraft(saved.output_text);
      setStatus("候选稿修改已保存。");
      return saved;
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "候选稿保存失败，请稍后重试");
      return null;
    } finally {
      setIsSavingContentGeneration(false);
    }
  };

  const adoptContentGeneration = async () => {
    if (!activeContentGeneration || activeContentGeneration.status !== "candidate") return;
    setIsAdoptingContentGeneration(true);
    setArtifactError("");
    setStatus("");
    try {
      let generation = activeContentGeneration;
      if (contentGenerationDraft.trim() !== activeContentGeneration.output_text) {
        const saved = await updateProjectEpisodeContentGeneration(
          projectId,
          selectedEpisodeNo,
          activeContentGeneration.id,
          contentGenerationDraft
        );
        generation = saved;
      }
      const result = await adoptProjectEpisodeContentGeneration(projectId, selectedEpisodeNo, generation.id);
      setEpisodeContent(result.content);
      setContentForm(episodeContentToForm(result.content));
      setEpisodeContentGenerations((current) =>
        current.map((item) => {
          if (item.id === result.generation.id) return result.generation;
          return item.status === "candidate" ? { ...item, status: "discarded" as const } : item;
        })
      );
      setContentEditorMode("current");
      setStatus(`第 ${selectedEpisodeNo} 集候选稿已采用；旧摘要和质检备注已清空，请重新填写摘要。`);
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "候选稿采用失败，请稍后重试");
    } finally {
      setIsAdoptingContentGeneration(false);
    }
  };

  const discardContentGeneration = async () => {
    if (!activeContentGeneration || activeContentGeneration.status !== "candidate") return;
    setArtifactError("");
    setStatus("");
    try {
      const discarded = await discardProjectEpisodeContentGeneration(
        projectId,
        selectedEpisodeNo,
        activeContentGeneration.id
      );
      setEpisodeContentGenerations((current) => current.map((item) => (item.id === discarded.id ? discarded : item)));
      setActiveContentGenerationId("");
      setContentGenerationDraft("");
      setContentEditorMode("current");
      setStatus("候选稿已放弃，正式正文未发生变化。");
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "候选稿放弃失败，请稍后重试");
    }
  };

  const saveEpisodeScript = async (event: FormEvent) => {
    event.preventDefault();
    setIsSaving(true);
    setArtifactError("");
    setStatus("");
    try {
      const saved = await updateProjectEpisodeScript(projectId, selectedEpisodeNo, {
        ...scriptForm,
        title: toOptional(scriptForm.title || "")
      });
      setEpisodeScript(saved);
      setScriptForm(episodeScriptToForm(saved));
      setStatus(`第 ${selectedEpisodeNo} 集剧本已保存，分镜和文案已标记为需要检查。`);
      void refreshEpisodeArtifacts(selectedEpisodeNo);
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "剧本保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const saveShot = async (event: FormEvent) => {
    event.preventDefault();
    setIsSaving(true);
    setArtifactError("");
    setStatus("");
    try {
      const payload = {
        shot_no: Number(shotForm.shot_no),
        scene: toOptional(shotForm.scene),
        visual_prompt: toOptional(shotForm.visual_prompt),
        camera: toOptional(shotForm.camera),
        duration_seconds: toOptionalNumber(shotForm.duration_seconds),
        dialogue_or_voiceover: toOptional(shotForm.dialogue_or_voiceover),
        status: shotForm.status
      };
      const saved = editingShotId
        ? await updateProjectStoryboardShot(projectId, selectedEpisodeNo, editingShotId, payload)
        : await createProjectStoryboardShot(projectId, selectedEpisodeNo, payload);
      setStoryboardShots((current) => replaceShot(current, saved));
      setStatus(`第 ${selectedEpisodeNo} 集分镜已保存。`);
      resetShotForm(replaceShot(storyboardShots, saved));
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "分镜保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const saveCopywriting = async (event: FormEvent) => {
    event.preventDefault();
    setIsSaving(true);
    setArtifactError("");
    setStatus("");
    try {
      const saved = await updateProjectCopywriting(projectId, selectedEpisodeNo, {
        subtitles: toOptional(copyForm.subtitles),
        platform_title: toOptional(copyForm.platform_title),
        platform_description: toOptional(copyForm.platform_description),
        publish_copy: toOptional(copyForm.publish_copy),
        status: copyForm.status
      });
      setCopywriting(saved);
      setCopyForm(copywritingToForm(saved));
      setStatus(`第 ${selectedEpisodeNo} 集文案已保存。`);
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "文案保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const startEditingWorldSnapshot = (snapshot: ProjectWorldSnapshot) => {
    setError("");
    setStatus("");
    setEditingCharacterSnapshotId("");
    setEditingWorldSnapshotId(snapshot.id);
    setWorldSnapshotForm(worldSnapshotToForm(snapshot));
  };

  const startEditingCharacterSnapshot = (snapshot: ProjectCharacterSnapshot) => {
    setError("");
    setStatus("");
    setEditingWorldSnapshotId("");
    setEditingCharacterSnapshotId(snapshot.id);
    setCharacterSnapshotForm(characterSnapshotToForm(snapshot));
  };

  const cancelWorldSnapshotEdit = () => {
    setEditingWorldSnapshotId("");
    setWorldSnapshotForm(emptyWorldSnapshotForm);
  };

  const cancelCharacterSnapshotEdit = () => {
    setEditingCharacterSnapshotId("");
    setCharacterSnapshotForm(emptyCharacterSnapshotForm);
  };

  const saveWorldSnapshot = async (event: FormEvent) => {
    event.preventDefault();
    if (!editingWorldSnapshotId) return;
    setError("");
    setStatus("");
    if (!worldSnapshotForm.name.trim()) {
      setError("项目世界观名称不能为空");
      return;
    }
    if (!worldSnapshotForm.genre.trim()) {
      setError("项目世界观题材不能为空");
      return;
    }
    if (!worldSnapshotForm.world_rules.trim()) {
      setError("项目世界观规则不能为空");
      return;
    }
    if (worldSnapshotForm.entries.some((entry) => !entry.title.trim() || !entry.content.trim())) {
      setError("项目世界观条目的标题和内容不能为空");
      return;
    }

    setSavingSnapshotId(editingWorldSnapshotId);
    try {
      const saved = await updateProjectWorldSnapshot(projectId, editingWorldSnapshotId, worldSnapshotFormToPayload(worldSnapshotForm));
      setWorldSnapshots((current) => replaceWorldSnapshot(current, saved));
      cancelWorldSnapshotEdit();
      setStatus("项目世界观已保存，故事文本和短剧制作已有内容已标记为需要检查。");
      refreshDownstreamAfterAssetChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "项目世界观保存失败");
    } finally {
      setSavingSnapshotId("");
    }
  };

  const saveCharacterSnapshot = async (event: FormEvent) => {
    event.preventDefault();
    if (!editingCharacterSnapshotId) return;
    setError("");
    setStatus("");
    if (!characterSnapshotForm.name.trim()) {
      setError("项目角色名不能为空");
      return;
    }
    if (!characterSnapshotForm.role_type.trim()) {
      setError("项目角色人物原型不能为空");
      return;
    }
    if (!characterSnapshotForm.identity.trim() && !characterSnapshotForm.goal.trim()) {
      setError("项目角色身份或目标至少填写一项");
      return;
    }

    setSavingSnapshotId(editingCharacterSnapshotId);
    try {
      const saved = await updateProjectCharacterSnapshot(projectId, editingCharacterSnapshotId, characterSnapshotFormToPayload(characterSnapshotForm));
      setCharacterSnapshots((current) => replaceCharacterSnapshot(current, saved));
      cancelCharacterSnapshotEdit();
      setStatus("项目角色已保存，故事文本和短剧制作已有内容已标记为需要检查。");
      refreshDownstreamAfterAssetChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "项目角色保存失败");
    } finally {
      setSavingSnapshotId("");
    }
  };

  const confirmPendingAction = async () => {
    const action = pendingConfirmation?.onConfirm;
    setPendingConfirmation(null);
    await action?.();
  };

  const removeWorldSnapshot = (snapshot: ProjectWorldSnapshot) => {
    setPendingConfirmation({
      title: "移除项目世界观？",
      description: `确定从项目中移除世界观“${snapshot.name}”吗？资产库原始世界观不会被删除。`,
      confirmLabel: "移除",
      destructive: true,
      onConfirm: () => executeRemoveWorldSnapshot(snapshot)
    });
  };

  const executeRemoveWorldSnapshot = async (snapshot: ProjectWorldSnapshot) => {
    setRemovingSnapshotId(snapshot.id);
    setError("");
    setStatus("");
    try {
      await deleteProjectWorldSnapshot(projectId, snapshot.id);
      setWorldSnapshots((current) => current.filter((item) => item.id !== snapshot.id));
      if (editingWorldSnapshotId === snapshot.id) {
        cancelWorldSnapshotEdit();
      }
      setStatus("世界观已从项目中移除，故事文本和短剧制作已有内容已标记为需要检查。");
      refreshDownstreamAfterAssetChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "世界观移除失败");
    } finally {
      setRemovingSnapshotId("");
    }
  };

  const removeCharacterSnapshot = (snapshot: ProjectCharacterSnapshot) => {
    setPendingConfirmation({
      title: "移除项目角色？",
      description: `确定从项目中移除角色“${snapshot.name}”吗？角色卡库原始角色不会被删除。`,
      confirmLabel: "移除",
      destructive: true,
      onConfirm: () => executeRemoveCharacterSnapshot(snapshot)
    });
  };

  const executeRemoveCharacterSnapshot = async (snapshot: ProjectCharacterSnapshot) => {
    setRemovingSnapshotId(snapshot.id);
    setError("");
    setStatus("");
    try {
      await deleteProjectCharacterSnapshot(projectId, snapshot.id);
      setCharacterSnapshots((current) => current.filter((item) => item.id !== snapshot.id));
      if (editingCharacterSnapshotId === snapshot.id) {
        cancelCharacterSnapshotEdit();
      }
      setStatus("角色已从项目中移除，故事文本和短剧制作已有内容已标记为需要检查。");
      refreshDownstreamAfterAssetChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "角色移除失败");
    } finally {
      setRemovingSnapshotId("");
    }
  };

  const openWorldPicker = async () => {
    setSelectedWorldId(null);
    setShowWorldPicker(true);
    setShowCharacterPicker(false);
    setIsLoadingPicker(true);
    try {
      const worlds = await listWorldBooks({ status: "active" });
      setAvailableWorlds(worlds);
    } catch {
      setAvailableWorlds([]);
    } finally {
      setIsLoadingPicker(false);
    }
  };

  const openCharacterPicker = async () => {
    setSelectedCharacterIds(new Set());
    setShowCharacterPicker(true);
    setShowWorldPicker(false);
    setIsLoadingPicker(true);
    try {
      const characters = await listCharacterCards({ status: "active" });
      setAvailableCharacters(characters);
    } catch {
      setAvailableCharacters([]);
    } finally {
      setIsLoadingPicker(false);
    }
  };

  const handleLoadWorld = async () => {
    if (!selectedWorldId) return;
    if (worldSnapshots.length > 0) {
      setError("该项目已加载世界观，每个项目只能加载一个世界观。请先移除当前项目世界观。");
      return;
    }
    setLoadingAssetId(selectedWorldId);
    setError("");
    setStatus("");
    try {
      await loadWorldBookToProject(projectId, selectedWorldId);
      setStatus("世界观已加载到项目，故事文本和短剧制作已有内容已标记为需要检查。");
      await refreshAssets();
      setShowWorldPicker(false);
      setSelectedWorldId(null);
      refreshDownstreamAfterAssetChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "世界观加载失败");
    } finally {
      setLoadingAssetId("");
    }
  };

  const handleLoadCharacters = async () => {
    if (selectedCharacterIds.size === 0) return;
    setIsBatchLoading(true);
    setError("");
    setStatus("");
    const ids = Array.from(selectedCharacterIds);
    let failedCount = 0;
    for (const characterCardId of ids) {
      try {
        await loadCharacterCardToProject(projectId, characterCardId);
      } catch {
        failedCount++;
      }
    }
    setIsBatchLoading(false);
    if (failedCount === 0) {
      setStatus(`已成功加载 ${ids.length} 个角色到项目，故事文本和短剧制作已有内容已标记为需要检查。`);
    } else if (failedCount < ids.length) {
      setStatus(`已加载 ${ids.length - failedCount} 个角色，${failedCount} 个加载失败；故事文本和短剧制作已有内容已标记为需要检查。`);
    } else {
      setError("所有角色加载失败，请重试。");
    }
    setSelectedCharacterIds(new Set());
    await refreshAssets();
    setShowCharacterPicker(false);
    refreshDownstreamAfterAssetChange();
  };

  const editShot = (shot: ProjectStoryboardShot) => {
    setEditingShotId(shot.id);
    setShotForm(shotToForm(shot));
  };

  const removeShot = (shot: ProjectStoryboardShot) => {
    setPendingConfirmation({
      title: "删除分镜镜头？",
      description: `确定删除第 ${shot.shot_no} 个镜头？删除后需要重新新增该镜头。`,
      confirmLabel: "删除",
      destructive: true,
      onConfirm: () => executeRemoveShot(shot)
    });
  };

  const executeRemoveShot = async (shot: ProjectStoryboardShot) => {
    setRemovingShotId(shot.id);
    setArtifactError("");
    setStatus("");
    try {
      await deleteProjectStoryboardShot(projectId, selectedEpisodeNo, shot.id);
      const nextShots = storyboardShots.filter((item) => item.id !== shot.id);
      setStoryboardShots(nextShots);
      resetShotForm(nextShots);
      setStatus("分镜已删除。");
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "分镜删除失败");
    } finally {
      setRemovingShotId("");
    }
  };

  const resetProjectForm = () => {
    if (!project) return;
    setError("");
    setStatus("");
    setProjectForm(projectToForm(project));
  };

  const resetShotForm = (shots = storyboardShots) => {
    setEditingShotId("");
    setShotForm({ ...emptyShotForm, shot_no: String(nextShotNo(shots)) });
  };

  const showAiPlaceholder = (label: string) => {
    setArtifactError("");
    setStatus(`${label}暂未接入，后续完善。`);
  };

  const episodeContentGenerationTypeLabel = (generationType: EpisodeContentGenerationType) => {
    if (generationType === "continue") return "续写";
    if (generationType === "polish") return "润色";
    return "正文创作";
  };

  return {
    projectId,
    mode,
    isLandingMode,
    visibleGroups,
    visibleStages,
    project,
    activeStage,
    setActiveStage,
    selectedEpisodeNo,
    setSelectedEpisodeNo,
    worldSnapshots,
    characterSnapshots,
    storyOutline,
    episodeOutlines,
    episodeContent,
    episodeContentGenerations,
    activeContentGeneration,
    contentGenerationType,
    setContentGenerationType,
    episodeScript,
    storyboardShots,
    copywriting,
    projectForm,
    setProjectForm,
    storyForm,
    setStoryForm,
    episodeForm,
    setEpisodeForm,
    contentForm,
    setContentForm,
    scriptForm,
    setScriptForm,
    shotForm,
    setShotForm,
    editingShotId,
    copyForm,
    setCopyForm,
    worldSnapshotForm,
    setWorldSnapshotForm,
    editingWorldSnapshotId,
    characterSnapshotForm,
    setCharacterSnapshotForm,
    editingCharacterSnapshotId,
    error,
    assetError,
    artifactError,
    status,
    isLoading,
    isLoadingAssets,
    isLoadingEpisodeArtifacts,
    isSaving,
    isGeneratingContent,
    isSavingContentGeneration,
    isAdoptingContentGeneration,
    savingSnapshotId,
    removingSnapshotId,
    removingShotId,
    pendingConfirmation,
    setPendingConfirmation,
    confirmPendingAction,
    showWorldPicker,
    setShowWorldPicker,
    showCharacterPicker,
    setShowCharacterPicker,
    availableWorlds,
    availableCharacters,
    isLoadingPicker,
    loadingAssetId,
    selectedWorldId,
    setSelectedWorldId,
    selectedCharacterIds,
    setSelectedCharacterIds,
    isBatchLoading,
    activeReferenceTab,
    setActiveReferenceTab,
    episodeCount,
    episodeDuration,
    totalDuration,
    loadedWorldIds,
    loadedCharacterIds,
    validationError,
    durationChanged,
    episodeRows,
    selectedEpisodeOutline,
    canGenerateEpisodeContent,
    canContinueEpisodeContent,
    canPolishEpisodeContent,
    activeWorkspaceGroup,
    currentWorkspaceGroup,
    filledEpisodeOutlineCount,
    storyOutlineStatus,
    episodeContentStatus,
    episodeScriptStatus,
    copywritingStatus,
    contentWordCount,
    previousEpisodeSummary,
    contentGenerationInstruction,
    setContentGenerationInstruction,
    contentGenerationDraft,
    setContentGenerationDraft,
    contentEditorMode,
    setContentEditorMode,
    showContentCreator,
    setShowContentCreator,
    saveProject,
    saveStoryOutline,
    saveEpisodeOutline,
    saveEpisodeContent,
    openEpisodeContentCreator,
    generateEpisodeContentCandidate,
    selectContentGeneration,
    saveContentGenerationDraft,
    adoptContentGeneration,
    discardContentGeneration,
    saveEpisodeScript,
    saveShot,
    saveCopywriting,
    startEditingWorldSnapshot,
    startEditingCharacterSnapshot,
    cancelWorldSnapshotEdit,
    cancelCharacterSnapshotEdit,
    saveWorldSnapshot,
    saveCharacterSnapshot,
    removeWorldSnapshot,
    removeCharacterSnapshot,
    openWorldPicker,
    openCharacterPicker,
    handleLoadWorld,
    handleLoadCharacters,
    editShot,
    removeShot,
    resetProjectForm,
    resetShotForm,
    showAiPlaceholder
  };
}

export type ProjectWorkbenchState = ReturnType<typeof useProjectWorkbench>;
