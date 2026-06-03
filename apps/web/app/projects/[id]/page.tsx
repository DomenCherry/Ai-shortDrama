"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import type { Dispatch, ReactNode, SetStateAction } from "react";
import { useParams } from "next/navigation";
import {
  createProjectStoryboardShot,
  deleteProjectCharacterSnapshot,
  deleteProjectStoryboardShot,
  deleteProjectWorldSnapshot,
  getProject,
  getProjectCopywriting,
  getProjectEpisodeContent,
  getProjectEpisodeScript,
  getProjectStoryOutline,
  listCharacterCards,
  listProjectCharacterSnapshots,
  listProjectEpisodeOutlines,
  listProjectStoryboardShots,
  listProjectWorldSnapshots,
  listWorldBooks,
  loadCharacterCardToProject,
  loadWorldBookToProject,
  ProjectArtifactStatus,
  ProjectCharacterSnapshot,
  ProjectCopywriting,
  ProjectEpisodeContent,
  ProjectEpisodeOutline,
  ProjectEpisodeScript,
  ProjectStoryboardShot,
  ProjectStoryOutline,
  ProjectSummary,
  ProjectWorldSnapshot,
  updateProject,
  updateProjectCharacterSnapshot,
  updateProjectCopywriting,
  updateProjectEpisodeContent,
  updateProjectEpisodeOutline,
  updateProjectEpisodeScript,
  updateProjectStoryboardShot,
  updateProjectStoryOutline,
  updateProjectWorldSnapshot,
  WorldBook,
  CharacterCard
} from "@/lib/api";

type Stage = "settings" | "assets" | "story" | "episodes" | "content" | "script" | "storyboard";

type ProjectForm = {
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

type WorldSnapshotForm = {
  name: string;
  genre: string;
  snapshot_content: string;
  entry_snapshot_content: string;
};

type CharacterSnapshotForm = {
  name: string;
  gender: "男" | "女";
  role_type: string;
  snapshot_content: string;
  visual_description: string;
  reference_image_url: string;
  reference_local_path: string;
};

type StoryOutlineForm = {
  logline: string;
  core_conflict: string;
  main_goal: string;
  character_arcs: string;
  ending_direction: string;
  notes: string;
  status: ProjectArtifactStatus;
};

type EpisodeOutlineForm = {
  title: string;
  synopsis: string;
  hook: string;
  conflict: string;
  reversal: string;
  cliffhanger: string;
  duration_minutes: string;
  status: ProjectArtifactStatus;
};

type EpisodeContentForm = {
  detailed_content: string;
  key_beats: string;
  status: ProjectArtifactStatus;
};

type EpisodeScriptForm = {
  scene_text: string;
  dialogue: string;
  action_notes: string;
  voiceover: string;
  status: ProjectArtifactStatus;
};

type ShotForm = {
  shot_no: string;
  scene: string;
  visual_prompt: string;
  camera: string;
  duration_seconds: string;
  dialogue_or_voiceover: string;
  status: ProjectArtifactStatus;
};

type CopywritingForm = {
  subtitles: string;
  platform_title: string;
  platform_description: string;
  publish_copy: string;
  status: ProjectArtifactStatus;
};

const stages: Array<{ key: Stage; label: string }> = [
  { key: "settings", label: "基础信息" },
  { key: "assets", label: "世界观与角色" },
  { key: "story", label: "故事大纲" },
  { key: "episodes", label: "分集大纲" },
  { key: "content", label: "单集内容" },
  { key: "script", label: "剧本" },
  { key: "storyboard", label: "分镜与文案" }
];

export default function ProjectWorkbenchPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [activeStage, setActiveStage] = useState<Stage>("settings");
  const [selectedEpisodeNo, setSelectedEpisodeNo] = useState(1);

  const [worldSnapshots, setWorldSnapshots] = useState<ProjectWorldSnapshot[]>([]);
  const [characterSnapshots, setCharacterSnapshots] = useState<ProjectCharacterSnapshot[]>([]);
  const [storyOutline, setStoryOutline] = useState<ProjectStoryOutline | null>(null);
  const [episodeOutlines, setEpisodeOutlines] = useState<ProjectEpisodeOutline[]>([]);
  const [episodeContent, setEpisodeContent] = useState<ProjectEpisodeContent | null>(null);
  const [episodeScript, setEpisodeScript] = useState<ProjectEpisodeScript | null>(null);
  const [storyboardShots, setStoryboardShots] = useState<ProjectStoryboardShot[]>([]);
  const [copywriting, setCopywriting] = useState<ProjectCopywriting | null>(null);

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
  const [savingSnapshotId, setSavingSnapshotId] = useState("");
  const [removingSnapshotId, setRemovingSnapshotId] = useState("");
  const [removingShotId, setRemovingShotId] = useState("");

  const [showWorldPicker, setShowWorldPicker] = useState(false);
  const [showCharacterPicker, setShowCharacterPicker] = useState(false);
  const [availableWorlds, setAvailableWorlds] = useState<WorldBook[]>([]);
  const [availableCharacters, setAvailableCharacters] = useState<CharacterCard[]>([]);
  const [isLoadingPicker, setIsLoadingPicker] = useState(false);
  const [loadingAssetId, setLoadingAssetId] = useState("");

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

  useEffect(() => {
    void refreshWorkbench();
  }, [projectId]);

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
      const [content, script, shots, copy] = await Promise.all([
        getProjectEpisodeContent(projectId, episodeNo),
        getProjectEpisodeScript(projectId, episodeNo),
        listProjectStoryboardShots(projectId, episodeNo),
        getProjectCopywriting(projectId, episodeNo)
      ]);
      setEpisodeContent(content);
      setEpisodeScript(script);
      setStoryboardShots(shots);
      setCopywriting(copy);
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
      setStatus("项目信息已保存，下游创作内容已标记为需要检查。");
      void refreshStoryAndEpisodes();
      void refreshEpisodeArtifacts(selectedEpisodeNo);
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
      const saved = await updateProjectStoryOutline(projectId, {
        logline: toOptional(storyForm.logline),
        core_conflict: toOptional(storyForm.core_conflict),
        main_goal: toOptional(storyForm.main_goal),
        character_arcs: toOptional(storyForm.character_arcs),
        ending_direction: toOptional(storyForm.ending_direction),
        notes: toOptional(storyForm.notes),
        status: storyForm.status
      });
      setStoryOutline(saved);
      setStoryForm(storyOutlineToForm(saved));
      setStatus("整体故事大纲已保存，下游分集和剧本已标记为需要检查。");
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
      setStatus(`第 ${selectedEpisodeNo} 集分集大纲已保存，下游内容已标记为需要检查。`);
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
        detailed_content: toOptional(contentForm.detailed_content),
        key_beats: toOptional(contentForm.key_beats),
        status: contentForm.status
      });
      setEpisodeContent(saved);
      setContentForm(episodeContentToForm(saved));
      setStatus(`第 ${selectedEpisodeNo} 集详细内容已保存，下游剧本和分镜已标记为需要检查。`);
      void refreshEpisodeArtifacts(selectedEpisodeNo);
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "单集内容保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const saveEpisodeScript = async (event: FormEvent) => {
    event.preventDefault();
    setIsSaving(true);
    setArtifactError("");
    setStatus("");
    try {
      const saved = await updateProjectEpisodeScript(projectId, selectedEpisodeNo, {
        scene_text: toOptional(scriptForm.scene_text),
        dialogue: toOptional(scriptForm.dialogue),
        action_notes: toOptional(scriptForm.action_notes),
        voiceover: toOptional(scriptForm.voiceover),
        status: scriptForm.status
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
    if (!worldSnapshotForm.snapshot_content.trim()) {
      setError("项目世界观基础设定不能为空");
      return;
    }
    if (!worldSnapshotForm.entry_snapshot_content.trim()) {
      setError("项目世界观条目快照不能为空");
      return;
    }

    setSavingSnapshotId(editingWorldSnapshotId);
    try {
      const saved = await updateProjectWorldSnapshot(projectId, editingWorldSnapshotId, {
        name: worldSnapshotForm.name,
        genre: worldSnapshotForm.genre,
        snapshot_content: worldSnapshotForm.snapshot_content,
        entry_snapshot_content: worldSnapshotForm.entry_snapshot_content
      });
      setWorldSnapshots((current) => replaceWorldSnapshot(current, saved));
      cancelWorldSnapshotEdit();
      setStatus("项目世界观已保存，下游创作内容已标记为需要检查。");
      void refreshStoryAndEpisodes();
      void refreshEpisodeArtifacts(selectedEpisodeNo);
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
    if (!characterSnapshotForm.snapshot_content.trim()) {
      setError("项目角色设定快照不能为空");
      return;
    }

    setSavingSnapshotId(editingCharacterSnapshotId);
    try {
      const saved = await updateProjectCharacterSnapshot(projectId, editingCharacterSnapshotId, {
        name: characterSnapshotForm.name,
        gender: characterSnapshotForm.gender,
        role_type: characterSnapshotForm.role_type,
        snapshot_content: characterSnapshotForm.snapshot_content,
        visual_description: toOptional(characterSnapshotForm.visual_description),
        reference_image_url: toOptional(characterSnapshotForm.reference_image_url),
        reference_local_path: toOptional(characterSnapshotForm.reference_local_path)
      });
      setCharacterSnapshots((current) => replaceCharacterSnapshot(current, saved));
      cancelCharacterSnapshotEdit();
      setStatus("项目角色已保存，下游创作内容已标记为需要检查。");
      void refreshStoryAndEpisodes();
      void refreshEpisodeArtifacts(selectedEpisodeNo);
    } catch (err) {
      setError(err instanceof Error ? err.message : "项目角色保存失败");
    } finally {
      setSavingSnapshotId("");
    }
  };

  const removeWorldSnapshot = async (snapshot: ProjectWorldSnapshot) => {
    if (!window.confirm(`确定从项目中移除世界观“${snapshot.name}”吗？资产库原始世界观不会被删除。`)) {
      return;
    }
    setRemovingSnapshotId(snapshot.id);
    setError("");
    setStatus("");
    try {
      await deleteProjectWorldSnapshot(projectId, snapshot.id);
      setWorldSnapshots((current) => current.filter((item) => item.id !== snapshot.id));
      if (editingWorldSnapshotId === snapshot.id) {
        cancelWorldSnapshotEdit();
      }
      setStatus("世界观已从项目中移除，下游创作内容已标记为需要检查。");
      void refreshStoryAndEpisodes();
      void refreshEpisodeArtifacts(selectedEpisodeNo);
    } catch (err) {
      setError(err instanceof Error ? err.message : "世界观移除失败");
    } finally {
      setRemovingSnapshotId("");
    }
  };

  const removeCharacterSnapshot = async (snapshot: ProjectCharacterSnapshot) => {
    if (!window.confirm(`确定从项目中移除角色“${snapshot.name}”吗？角色卡库原始角色不会被删除。`)) {
      return;
    }
    setRemovingSnapshotId(snapshot.id);
    setError("");
    setStatus("");
    try {
      await deleteProjectCharacterSnapshot(projectId, snapshot.id);
      setCharacterSnapshots((current) => current.filter((item) => item.id !== snapshot.id));
      if (editingCharacterSnapshotId === snapshot.id) {
        cancelCharacterSnapshotEdit();
      }
      setStatus("角色已从项目中移除，下游创作内容已标记为需要检查。");
      void refreshStoryAndEpisodes();
      void refreshEpisodeArtifacts(selectedEpisodeNo);
    } catch (err) {
      setError(err instanceof Error ? err.message : "角色移除失败");
    } finally {
      setRemovingSnapshotId("");
    }
  };

  const openWorldPicker = async () => {
    setShowWorldPicker(true);
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
    setShowCharacterPicker(true);
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

  const handleLoadWorld = async (worldBookId: string) => {
    if (worldSnapshots.length > 0) {
      setError("该项目已加载世界观，每个项目只能加载一个世界观。请先移除当前项目世界观。");
      return;
    }
    setLoadingAssetId(worldBookId);
    setError("");
    setStatus("");
    try {
      await loadWorldBookToProject(projectId, worldBookId);
      setStatus("世界观已加载到项目，下游创作内容已标记为需要检查。");
      await refreshAssets();
      void refreshStoryAndEpisodes();
      void refreshEpisodeArtifacts(selectedEpisodeNo);
    } catch (err) {
      setError(err instanceof Error ? err.message : "世界观加载失败");
    } finally {
      setLoadingAssetId("");
    }
  };

  const handleLoadCharacter = async (characterCardId: string) => {
    setLoadingAssetId(characterCardId);
    setError("");
    setStatus("");
    try {
      await loadCharacterCardToProject(projectId, characterCardId);
      setStatus("角色已加载到项目，下游创作内容已标记为需要检查。");
      await refreshAssets();
      void refreshStoryAndEpisodes();
      void refreshEpisodeArtifacts(selectedEpisodeNo);
    } catch (err) {
      setError(err instanceof Error ? err.message : "角色加载失败");
    } finally {
      setLoadingAssetId("");
    }
  };

  const editShot = (shot: ProjectStoryboardShot) => {
    setEditingShotId(shot.id);
    setShotForm(shotToForm(shot));
  };

  const removeShot = async (shot: ProjectStoryboardShot) => {
    if (!window.confirm(`确定删除第 ${shot.shot_no} 个镜头？`)) {
      return;
    }
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

  if (isLoading) {
    return (
      <div className="stack">
        <header className="page-header">
          <div>
            <h1 className="page-title">项目工作台</h1>
            <p className="page-description">正在加载项目资料...</p>
          </div>
        </header>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="stack">
        <header className="page-header">
          <div>
            <h1 className="page-title">项目工作台</h1>
            <p className="page-description">无法读取项目资料。</p>
          </div>
          <Link className="button secondary" href="/">
            返回项目管理
          </Link>
        </header>
        {error ? <div className="error">{error}</div> : null}
      </div>
    );
  }

  return (
    <div className="stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">{project.title}</h1>
          <p className="page-description">
            按项目设定、资产、大纲、分集、剧本、分镜文案推进短剧创作。上游变更后，下游内容会提示需要检查。
          </p>
        </div>
        <Link className="button secondary" href="/">
          返回项目管理
        </Link>
      </header>

      <section className="panel stack">
        <div className="section-heading">
          <h2>项目概览</h2>
          <span className={`status-badge status-${project.status === "draft" ? "draft" : "active"}`}>
            {project.status === "draft" ? "草稿" : project.status}
          </span>
        </div>
        <div className="metric-grid">
          <Metric label="题材" value={project.genre || "未设置"} />
          <Metric label="平台" value={project.target_platform || "未设置"} />
          <Metric label="集数" value={`${project.episode_count} 集`} />
          <Metric label="单集时长" value={`${formatNumber(project.episode_duration)} 分钟`} />
          <Metric label="总时长" value={`${formatNumber(project.total_duration)} 分钟`} />
        </div>
        <p>{project.idea}</p>
        <p className="hint">更新时间：{new Date(project.updated_at).toLocaleString()}</p>
      </section>

      <nav className="stage-tabs" aria-label="项目工作台阶段">
        {stages.map((stage) => (
          <button
            className={`stage-tab ${activeStage === stage.key ? "active" : ""}`}
            type="button"
            key={stage.key}
            onClick={() => setActiveStage(stage.key)}
          >
            {stage.label}
          </button>
        ))}
      </nav>

      {error ? <div className="error">{error}</div> : null}
      {status ? <div className="success">{status}</div> : null}
      {assetError ? <div className="error">{assetError}</div> : null}
      {artifactError ? <div className="error">{artifactError}</div> : null}

      {activeStage === "settings" ? (
        <form className="panel stack" onSubmit={saveProject}>
          <div className="section-heading">
            <h2>项目设定</h2>
            <button className="button secondary" type="button" onClick={resetProjectForm} disabled={isSaving}>
              还原
            </button>
          </div>
          <TextArea label="创意描述" value={projectForm.idea} onChange={(value) => setProjectFormValue("idea", value, setProjectForm)} />
          <div className="grid-2">
            <TextInput label="项目名称" value={projectForm.title} onChange={(value) => setProjectFormValue("title", value, setProjectForm)} />
            <TextInput label="目标平台" value={projectForm.target_platform} onChange={(value) => setProjectFormValue("target_platform", value, setProjectForm)} />
            <TextInput label="题材类型" value={projectForm.genre} onChange={(value) => setProjectFormValue("genre", value, setProjectForm)} />
            <TextInput label="目标受众" value={projectForm.target_audience} onChange={(value) => setProjectFormValue("target_audience", value, setProjectForm)} />
            <TextInput label="内容风格" value={projectForm.style} onChange={(value) => setProjectFormValue("style", value, setProjectForm)} />
            <TextInput label="备注" value={projectForm.remark} onChange={(value) => setProjectFormValue("remark", value, setProjectForm)} />
          </div>
          <div className="grid-2">
            <NumberInput label="集数" min="1" step="1" value={projectForm.episode_count} onChange={(value) => setProjectFormValue("episode_count", value, setProjectForm)} />
            <NumberInput label="单集时长（分钟）" min="0.1" max="2" step="0.1" value={projectForm.episode_duration} onChange={(value) => setProjectFormValue("episode_duration", value, setProjectForm)} />
          </div>
          <div className="summary-box">
            <strong>总时长：</strong>
            {Number.isFinite(totalDuration) ? `${formatNumber(totalDuration)} 分钟` : "请填写集数和单集时长"}
            {Number.isFinite(episodeDuration) && episodeDuration > 0 ? (
              <span className="hint">，单集约 {formatNumber(episodeDuration * 60)} 秒</span>
            ) : null}
          </div>
          {durationChanged ? <div className="warning-text">修改集数或单集时长会让已有大纲、分集、剧本、分镜进入需要检查状态。</div> : null}
          {validationError ? <div className="error">{validationError}</div> : null}
          <div className="actions">
            <button className="button" type="submit" disabled={isSaving || Boolean(validationError)}>
              {isSaving ? "保存中..." : "保存项目设定"}
            </button>
          </div>
        </form>
      ) : null}

      {activeStage === "assets" ? (
        <div className="grid-2">
          <AssetSection
            title="项目世界观"
            linkHref="/world-books"
            linkLabel="前往世界观库"
            isLoading={isLoadingAssets}
            emptyText="尚未加载世界观。点击下方按钮从世界观库中选择并加载。"
            onPick={openWorldPicker}
            pickLabel="加载世界观"
            pickDisabled={worldSnapshots.length > 0}
          >
            {worldSnapshots.map((snapshot) => (
              <article className="asset-card" key={snapshot.id}>
                <div className="asset-card-main">
                  <div className="asset-card-title">
                    <strong>{snapshot.name}</strong>
                    <span className="status-badge status-active">已加载 v{snapshot.source_version}</span>
                  </div>
                  <div className="hint">{snapshot.genre}</div>
                  <p>{worldSnapshotSummary(snapshot)}</p>
                  <p className="hint">加载时间：{new Date(snapshot.loaded_at).toLocaleString()}</p>
                </div>
                <div className="asset-card-actions">
                  <button className="button secondary" type="button" onClick={() => startEditingWorldSnapshot(snapshot)}>
                    编辑项目世界观
                  </button>
                  <button
                    className="button danger"
                    type="button"
                    onClick={() => void removeWorldSnapshot(snapshot)}
                    disabled={removingSnapshotId === snapshot.id}
                  >
                    {removingSnapshotId === snapshot.id ? "移除中..." : "从项目移除"}
                  </button>
                </div>
                {editingWorldSnapshotId === snapshot.id ? (
                  <form className="form-section stack" onSubmit={saveWorldSnapshot}>
                    <div className="warning-text">此处只修改当前项目世界观，不会修改世界观库原始内容。</div>
                    <div className="grid-2">
                      <TextInput label="项目世界观名称" value={worldSnapshotForm.name} onChange={(value) => setWorldSnapshotFormValue("name", value, setWorldSnapshotForm)} />
                      <TextInput label="题材类型" value={worldSnapshotForm.genre} onChange={(value) => setWorldSnapshotFormValue("genre", value, setWorldSnapshotForm)} />
                      <TextArea label="基础设定快照" value={worldSnapshotForm.snapshot_content} onChange={(value) => setWorldSnapshotFormValue("snapshot_content", value, setWorldSnapshotForm)} />
                      <TextArea label="条目快照" value={worldSnapshotForm.entry_snapshot_content} onChange={(value) => setWorldSnapshotFormValue("entry_snapshot_content", value, setWorldSnapshotForm)} />
                    </div>
                    <div className="actions">
                      <button className="button secondary" type="button" onClick={cancelWorldSnapshotEdit} disabled={savingSnapshotId === snapshot.id}>
                        取消
                      </button>
                      <button className="button" type="submit" disabled={savingSnapshotId === snapshot.id}>
                        {savingSnapshotId === snapshot.id ? "保存中..." : "保存项目世界观"}
                      </button>
                    </div>
                  </form>
                ) : null}
              </article>
            ))}
          </AssetSection>

          {showWorldPicker ? (
            <div className="panel stack picker-panel">
              <div className="section-heading">
                <h3>选择世界观</h3>
                <button className="button secondary" type="button" onClick={() => setShowWorldPicker(false)}>
                  关闭
                </button>
              </div>
              {isLoadingPicker ? (
                <div className="empty-state">正在加载可用世界观...</div>
              ) : availableWorlds.length === 0 ? (
                <div className="empty-state">
                  没有可用的世界观。
                  <Link href="/world-books/new" className="button secondary" style={{ marginTop: "0.5rem", display: "inline-block" }}>
                    创建世界观
                  </Link>
                </div>
              ) : (
                <div className="asset-list">
                  {worldSnapshots.length > 0 ? <div className="warning-text">当前项目已加载世界观，每个项目只能加载一个世界观。</div> : null}
                  {availableWorlds.map((wb) => {
                    const hasProjectWorld = worldSnapshots.length > 0;
                    const isLoaded = loadedWorldIds.has(wb.id);
                    const isDisabled = hasProjectWorld || isLoaded;
                    return (
                      <article className={`asset-card ${isDisabled ? "asset-card-disabled" : ""}`} key={wb.id}>
                        <div className="asset-card-main">
                          <div className="asset-card-title">
                            <strong>{wb.name}</strong>
                            {hasProjectWorld ? (
                              <span className="status-badge status-active">{isLoaded ? "已加载" : "不可加载"}</span>
                            ) : (
                              <span className="status-badge status-draft">{isLoaded ? "已加载" : "可用"}</span>
                            )}
                          </div>
                          <div className="hint">{wb.genre} · v{wb.version}</div>
                          <p>{wb.summary || wb.world_rules || "无简介"}</p>
                        </div>
                        <div className="asset-card-actions">
                          <button
                            className="button"
                            type="button"
                            disabled={isDisabled || loadingAssetId === wb.id}
                            onClick={() => void handleLoadWorld(wb.id)}
                          >
                            {loadingAssetId === wb.id ? "加载中..." : isDisabled ? "不可加载" : "加载到项目"}
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
              <div className="hint" style={{ textAlign: "center" }}>
                <Link href="/world-books">前往世界观库管理</Link>
              </div>
            </div>
          ) : null}

          <AssetSection
            title="项目角色"
            linkHref="/character-cards"
            linkLabel="前往角色卡库"
            isLoading={isLoadingAssets}
            emptyText="尚未加载角色。点击下方按钮从角色卡库中选择并加载。"
            onPick={openCharacterPicker}
            pickLabel="加载角色"
          >
            {characterSnapshots.map((snapshot) => (
              <article className="asset-card" key={snapshot.id}>
                <div className="asset-card-main">
                  <div className="asset-card-title">
                    <strong>{snapshot.name}</strong>
                    <span className="status-badge status-active">已加载 v{snapshot.source_version}</span>
                  </div>
                  <div className="hint">
                    {snapshot.gender} · {snapshot.role_type}
                  </div>
                  <p>{snapshot.visual_description || characterSnapshotSummary(snapshot)}</p>
                  <p className="hint">加载时间：{new Date(snapshot.loaded_at).toLocaleString()}</p>
                </div>
                <div className="asset-card-actions">
                  <button className="button secondary" type="button" onClick={() => startEditingCharacterSnapshot(snapshot)}>
                    编辑项目角色
                  </button>
                  <button
                    className="button danger"
                    type="button"
                    onClick={() => void removeCharacterSnapshot(snapshot)}
                    disabled={removingSnapshotId === snapshot.id}
                  >
                    {removingSnapshotId === snapshot.id ? "移除中..." : "从项目移除"}
                  </button>
                </div>
                {editingCharacterSnapshotId === snapshot.id ? (
                  <form className="form-section stack" onSubmit={saveCharacterSnapshot}>
                    <div className="warning-text">此处只修改当前项目角色，不会修改角色卡库原始内容。</div>
                    <div className="grid-2">
                      <TextInput label="项目角色名" value={characterSnapshotForm.name} onChange={(value) => setCharacterSnapshotFormValue("name", value, setCharacterSnapshotForm)} />
                      <div className="field">
                        <label>性别</label>
                        <select
                          value={characterSnapshotForm.gender}
                          onChange={(event) => setCharacterSnapshotFormValue("gender", event.target.value as "男" | "女", setCharacterSnapshotForm)}
                        >
                          <option value="女">女</option>
                          <option value="男">男</option>
                        </select>
                      </div>
                      <TextInput label="人物原型 / 项目定位" value={characterSnapshotForm.role_type} onChange={(value) => setCharacterSnapshotFormValue("role_type", value, setCharacterSnapshotForm)} />
                      <TextArea label="项目角色设定快照" value={characterSnapshotForm.snapshot_content} onChange={(value) => setCharacterSnapshotFormValue("snapshot_content", value, setCharacterSnapshotForm)} />
                      <TextArea label="项目内视觉描述" value={characterSnapshotForm.visual_description} onChange={(value) => setCharacterSnapshotFormValue("visual_description", value, setCharacterSnapshotForm)} />
                      <TextInput label="参考图 URL" value={characterSnapshotForm.reference_image_url} onChange={(value) => setCharacterSnapshotFormValue("reference_image_url", value, setCharacterSnapshotForm)} />
                      <TextInput label="参考图本地路径" value={characterSnapshotForm.reference_local_path} onChange={(value) => setCharacterSnapshotFormValue("reference_local_path", value, setCharacterSnapshotForm)} />
                    </div>
                    <div className="actions">
                      <button className="button secondary" type="button" onClick={cancelCharacterSnapshotEdit} disabled={savingSnapshotId === snapshot.id}>
                        取消
                      </button>
                      <button className="button" type="submit" disabled={savingSnapshotId === snapshot.id}>
                        {savingSnapshotId === snapshot.id ? "保存中..." : "保存项目角色"}
                      </button>
                    </div>
                  </form>
                ) : null}
              </article>
            ))}
          </AssetSection>

          {showCharacterPicker ? (
            <div className="panel stack picker-panel">
              <div className="section-heading">
                <h3>选择角色卡</h3>
                <button className="button secondary" type="button" onClick={() => setShowCharacterPicker(false)}>
                  关闭
                </button>
              </div>
              {isLoadingPicker ? (
                <div className="empty-state">正在加载可用角色卡...</div>
              ) : availableCharacters.length === 0 ? (
                <div className="empty-state">
                  没有可用的角色卡。
                  <Link href="/character-cards/new" className="button secondary" style={{ marginTop: "0.5rem", display: "inline-block" }}>
                    创建角色卡
                  </Link>
                </div>
              ) : (
                <div className="asset-list">
                  {availableCharacters.map((cc) => {
                    const isLoaded = loadedCharacterIds.has(cc.id);
                    return (
                      <article className={`asset-card ${isLoaded ? "asset-card-disabled" : ""}`} key={cc.id}>
                        <div className="asset-card-main">
                          <div className="asset-card-title">
                            <strong>{cc.name}</strong>
                            {isLoaded ? (
                              <span className="status-badge status-active">已加载</span>
                            ) : (
                              <span className="status-badge status-draft">可用</span>
                            )}
                          </div>
                          <div className="hint">{cc.gender} · {cc.role_type} · v{cc.version}</div>
                          <p>{cc.identity || cc.background || "无简介"}</p>
                        </div>
                        <div className="asset-card-actions">
                          <button
                            className="button"
                            type="button"
                            disabled={isLoaded || loadingAssetId === cc.id}
                            onClick={() => void handleLoadCharacter(cc.id)}
                          >
                            {loadingAssetId === cc.id ? "加载中..." : isLoaded ? "已加载" : "加载到项目"}
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
              <div className="hint" style={{ textAlign: "center" }}>
                <Link href="/character-cards">前往角色卡库管理</Link>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      {activeStage === "story" ? (
        <form className="panel stack" onSubmit={saveStoryOutline}>
          <SectionTitle title="整体故事大纲" status={storyOutline?.status ?? storyForm.status} />
          <div className="grid-2">
            <TextArea label="一句话故事" value={storyForm.logline} onChange={(value) => setStoryFormValue("logline", value, setStoryForm)} />
            <TextArea label="核心冲突" value={storyForm.core_conflict} onChange={(value) => setStoryFormValue("core_conflict", value, setStoryForm)} />
            <TextArea label="主线目标" value={storyForm.main_goal} onChange={(value) => setStoryFormValue("main_goal", value, setStoryForm)} />
            <TextArea label="人物弧光" value={storyForm.character_arcs} onChange={(value) => setStoryFormValue("character_arcs", value, setStoryForm)} />
            <TextArea label="结局方向" value={storyForm.ending_direction} onChange={(value) => setStoryFormValue("ending_direction", value, setStoryForm)} />
            <TextArea label="补充说明" value={storyForm.notes} onChange={(value) => setStoryFormValue("notes", value, setStoryForm)} />
          </div>
          <StatusSelect value={storyForm.status} onChange={(value) => setStoryFormValue("status", value, setStoryForm)} />
          <div className="actions">
            <button className="button" type="submit" disabled={isSaving}>
              {isSaving ? "保存中..." : "保存整体大纲"}
            </button>
          </div>
        </form>
      ) : null}

      {activeStage === "episodes" ? (
        <section className="panel stack">
          <SectionTitle title="分集大纲" status={episodeOutlines.find((outline) => outline.episode_no === selectedEpisodeNo)?.status ?? episodeForm.status} />
          <div className="episode-workspace">
            <aside className="episode-index" aria-label="分集列表">
              <EpisodePicker episodeCount={project.episode_count} value={selectedEpisodeNo} onChange={setSelectedEpisodeNo} />
              <div className="episode-index-list">
                {episodeRows.map((row) => (
                  <button
                    className={`episode-index-item ${selectedEpisodeNo === row.episodeNo ? "active" : ""}`}
                    type="button"
                    key={row.episodeNo}
                    onClick={() => setSelectedEpisodeNo(row.episodeNo)}
                    aria-current={selectedEpisodeNo === row.episodeNo ? "true" : undefined}
                  >
                    <span className="episode-index-main">
                      <strong>第 {row.episodeNo} 集</strong>
                      <span>{row.outline?.title || "未填写标题"}</span>
                    </span>
                    <span className="episode-index-meta">
                      <ArtifactStatusBadge status={row.outline?.status ?? "draft"} />
                    </span>
                    <span className="episode-index-summary">{row.outline?.synopsis || "尚未填写本集梗概"}</span>
                  </button>
                ))}
              </div>
            </aside>

            <form className="episode-editor stack" onSubmit={saveEpisodeOutline}>
              <div className="episode-editor-heading">
                <h3>编辑第 {selectedEpisodeNo} 集</h3>
                <ArtifactStatusBadge status={episodeOutlines.find((outline) => outline.episode_no === selectedEpisodeNo)?.status ?? episodeForm.status} />
              </div>
              <div className="grid-2">
                <TextInput label="标题" value={episodeForm.title} onChange={(value) => setEpisodeFormValue("title", value, setEpisodeForm)} />
                <NumberInput label="预计时长（分钟）" min="0.1" step="0.1" value={episodeForm.duration_minutes} onChange={(value) => setEpisodeFormValue("duration_minutes", value, setEpisodeForm)} />
                <TextArea label="本集梗概" value={episodeForm.synopsis} onChange={(value) => setEpisodeFormValue("synopsis", value, setEpisodeForm)} />
                <TextArea label="开场钩子" value={episodeForm.hook} onChange={(value) => setEpisodeFormValue("hook", value, setEpisodeForm)} />
                <TextArea label="本集冲突" value={episodeForm.conflict} onChange={(value) => setEpisodeFormValue("conflict", value, setEpisodeForm)} />
                <TextArea label="反转" value={episodeForm.reversal} onChange={(value) => setEpisodeFormValue("reversal", value, setEpisodeForm)} />
                <TextArea label="结尾悬念" value={episodeForm.cliffhanger} onChange={(value) => setEpisodeFormValue("cliffhanger", value, setEpisodeForm)} />
              </div>
              <StatusSelect value={episodeForm.status} onChange={(value) => setEpisodeFormValue("status", value, setEpisodeForm)} />
              <div className="actions">
                <button className="button" type="submit" disabled={isSaving}>
                  {isSaving ? "保存中..." : "保存分集大纲"}
                </button>
              </div>
            </form>
          </div>
        </section>
      ) : null}

      {activeStage === "content" ? (
        <form className="panel stack" onSubmit={saveEpisodeContent}>
          <SectionTitle title="单集详细内容" status={episodeContent?.status ?? contentForm.status} />
          <EpisodePicker episodeCount={project.episode_count} value={selectedEpisodeNo} onChange={setSelectedEpisodeNo} />
          {isLoadingEpisodeArtifacts ? <div className="empty-state">正在加载单集内容...</div> : null}
          <TextArea label="详细剧情内容" value={contentForm.detailed_content} onChange={(value) => setContentFormValue("detailed_content", value, setContentForm)} />
          <TextArea label="关键剧情节拍" value={contentForm.key_beats} onChange={(value) => setContentFormValue("key_beats", value, setContentForm)} />
          <StatusSelect value={contentForm.status} onChange={(value) => setContentFormValue("status", value, setContentForm)} />
          <div className="actions">
            <button className="button" type="submit" disabled={isSaving}>
              {isSaving ? "保存中..." : "保存单集内容"}
            </button>
          </div>
        </form>
      ) : null}

      {activeStage === "script" ? (
        <form className="panel stack" onSubmit={saveEpisodeScript}>
          <SectionTitle title="单集剧本" status={episodeScript?.status ?? scriptForm.status} />
          <EpisodePicker episodeCount={project.episode_count} value={selectedEpisodeNo} onChange={setSelectedEpisodeNo} />
          {isLoadingEpisodeArtifacts ? <div className="empty-state">正在加载剧本...</div> : null}
          <div className="grid-2">
            <TextArea label="场景说明" value={scriptForm.scene_text} onChange={(value) => setScriptFormValue("scene_text", value, setScriptForm)} />
            <TextArea label="对白" value={scriptForm.dialogue} onChange={(value) => setScriptFormValue("dialogue", value, setScriptForm)} />
            <TextArea label="动作说明" value={scriptForm.action_notes} onChange={(value) => setScriptFormValue("action_notes", value, setScriptForm)} />
            <TextArea label="旁白" value={scriptForm.voiceover} onChange={(value) => setScriptFormValue("voiceover", value, setScriptForm)} />
          </div>
          <StatusSelect value={scriptForm.status} onChange={(value) => setScriptFormValue("status", value, setScriptForm)} />
          <div className="actions">
            <button className="button" type="submit" disabled={isSaving}>
              {isSaving ? "保存中..." : "保存剧本"}
            </button>
          </div>
        </form>
      ) : null}

      {activeStage === "storyboard" ? (
        <section className="panel stack">
          <SectionTitle title="分镜与文案" status={copywriting?.status ?? copyForm.status} />
          <EpisodePicker episodeCount={project.episode_count} value={selectedEpisodeNo} onChange={setSelectedEpisodeNo} />
          {isLoadingEpisodeArtifacts ? <div className="empty-state">正在加载分镜和文案...</div> : null}

          <div className="grid-2">
            <div className="stack">
              <div className="section-heading">
                <h3>镜头列表</h3>
                <button className="button secondary" type="button" onClick={() => resetShotForm()}>
                  新增镜头
                </button>
              </div>
              {storyboardShots.length === 0 ? (
                <div className="empty-state">当前集还没有分镜镜头。</div>
              ) : (
                <div className="asset-list">
                  {storyboardShots.map((shot) => (
                    <article className="asset-card" key={shot.id}>
                      <div className="asset-card-title">
                        <strong>镜头 {shot.shot_no}</strong>
                        <ArtifactStatusBadge status={shot.status} />
                      </div>
                      <p>{shot.scene || "未填写场景"}</p>
                      <p className="hint">{shot.visual_prompt || "未填写画面提示词"}</p>
                      <div className="asset-card-actions">
                        <button className="button secondary" type="button" onClick={() => editShot(shot)}>
                          编辑
                        </button>
                        <button className="button danger" type="button" onClick={() => void removeShot(shot)} disabled={removingShotId === shot.id}>
                          {removingShotId === shot.id ? "删除中..." : "删除"}
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>

            <form className="stack" onSubmit={saveShot}>
              <h3>{editingShotId ? "编辑镜头" : "新增镜头"}</h3>
              <div className="grid-2">
                <NumberInput label="镜头序号" min="1" step="1" value={shotForm.shot_no} onChange={(value) => setShotFormValue("shot_no", value, setShotForm)} />
                <NumberInput label="镜头时长（秒）" min="0.1" step="0.1" value={shotForm.duration_seconds} onChange={(value) => setShotFormValue("duration_seconds", value, setShotForm)} />
              </div>
              <TextArea label="场景/画面" value={shotForm.scene} onChange={(value) => setShotFormValue("scene", value, setShotForm)} />
              <TextArea label="画面提示词" value={shotForm.visual_prompt} onChange={(value) => setShotFormValue("visual_prompt", value, setShotForm)} />
              <TextArea label="镜头/机位" value={shotForm.camera} onChange={(value) => setShotFormValue("camera", value, setShotForm)} />
              <TextArea label="对白或旁白" value={shotForm.dialogue_or_voiceover} onChange={(value) => setShotFormValue("dialogue_or_voiceover", value, setShotForm)} />
              <StatusSelect value={shotForm.status} onChange={(value) => setShotFormValue("status", value, setShotForm)} />
              <div className="actions">
                <button className="button secondary" type="button" onClick={() => resetShotForm()}>
                  清空
                </button>
                <button className="button" type="submit" disabled={isSaving || !Number.isFinite(Number(shotForm.shot_no))}>
                  {isSaving ? "保存中..." : "保存镜头"}
                </button>
              </div>
            </form>
          </div>

          <form className="stack form-section" onSubmit={saveCopywriting}>
            <h3>字幕与发布文案</h3>
            <div className="grid-2">
              <TextArea label="字幕/剧情内文案" value={copyForm.subtitles} onChange={(value) => setCopyFormValue("subtitles", value, setCopyForm)} />
              <TextInput label="平台标题" value={copyForm.platform_title} onChange={(value) => setCopyFormValue("platform_title", value, setCopyForm)} />
              <TextArea label="平台简介" value={copyForm.platform_description} onChange={(value) => setCopyFormValue("platform_description", value, setCopyForm)} />
              <TextArea label="发布文案" value={copyForm.publish_copy} onChange={(value) => setCopyFormValue("publish_copy", value, setCopyForm)} />
            </div>
            <StatusSelect value={copyForm.status} onChange={(value) => setCopyFormValue("status", value, setCopyForm)} />
            <div className="actions">
              <button className="button" type="submit" disabled={isSaving}>
                {isSaving ? "保存中..." : "保存文案"}
              </button>
            </div>
          </form>
        </section>
      ) : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-item">
      <span className="hint">{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SectionTitle({ title, status }: { title: string; status: ProjectArtifactStatus }) {
  return (
    <div className="section-heading">
      <h2>{title}</h2>
      <ArtifactStatusBadge status={status} />
    </div>
  );
}

function ArtifactStatusBadge({ status }: { status: ProjectArtifactStatus }) {
  return <span className={`status-badge ${artifactStatusClass(status)}`}>{artifactStatusLabel(status)}</span>;
}

function AssetSection({
  title,
  linkHref,
  linkLabel,
  isLoading,
  emptyText,
  onPick,
  pickLabel,
  pickDisabled,
  children
}: {
  title: string;
  linkHref: string;
  linkLabel: string;
  isLoading: boolean;
  emptyText: string;
  onPick?: () => void;
  pickLabel?: string;
  pickDisabled?: boolean;
  children: ReactNode;
}) {
  const childArray = Array.isArray(children) ? children : [children];
  return (
    <section className="panel stack">
      <div className="section-heading">
        <h2>{title}</h2>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {onPick && pickLabel ? (
            <button className="button" type="button" onClick={onPick} disabled={pickDisabled}>
              {pickLabel}
            </button>
          ) : null}
          <Link className="button secondary" href={linkHref}>
            {linkLabel}
          </Link>
        </div>
      </div>
      {isLoading ? (
        <div className="empty-state">正在加载项目资产...</div>
      ) : childArray.length === 0 ? (
        <div className="empty-state">{emptyText}</div>
      ) : (
        <div className="asset-list asset-list-wide">{children}</div>
      )}
    </section>
  );
}

function EpisodePicker({ episodeCount, value, onChange }: { episodeCount: number; value: number; onChange: (value: number) => void }) {
  return (
    <div className="field compact-field">
      <label>当前集数</label>
      <select value={value} onChange={(event) => onChange(Number(event.target.value))}>
        {Array.from({ length: episodeCount }, (_, index) => index + 1).map((episodeNo) => (
          <option value={episodeNo} key={episodeNo}>
            第 {episodeNo} 集
          </option>
        ))}
      </select>
    </div>
  );
}

function TextInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div className="field">
      <label>{label}</label>
      <input value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function NumberInput({
  label,
  value,
  onChange,
  min,
  max,
  step
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  min?: string;
  max?: string;
  step?: string;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      <input type="number" min={min} max={max} step={step} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function TextArea({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div className="field">
      <label>{label}</label>
      <textarea value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function StatusSelect({ value, onChange }: { value: ProjectArtifactStatus; onChange: (value: ProjectArtifactStatus) => void }) {
  return (
    <div className="field compact-field">
      <label>状态</label>
      <select value={value} onChange={(event) => onChange(event.target.value as ProjectArtifactStatus)}>
        <option value="draft">草稿</option>
        <option value="confirmed">已确认</option>
        <option value="needs_review">需要检查</option>
      </select>
    </div>
  );
}

const emptyProjectForm: ProjectForm = {
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

const emptyWorldSnapshotForm: WorldSnapshotForm = {
  name: "",
  genre: "",
  snapshot_content: "",
  entry_snapshot_content: ""
};

const emptyCharacterSnapshotForm: CharacterSnapshotForm = {
  name: "",
  gender: "女",
  role_type: "",
  snapshot_content: "",
  visual_description: "",
  reference_image_url: "",
  reference_local_path: ""
};

const emptyStoryForm: StoryOutlineForm = {
  logline: "",
  core_conflict: "",
  main_goal: "",
  character_arcs: "",
  ending_direction: "",
  notes: "",
  status: "draft"
};

const emptyEpisodeForm: EpisodeOutlineForm = {
  title: "",
  synopsis: "",
  hook: "",
  conflict: "",
  reversal: "",
  cliffhanger: "",
  duration_minutes: "",
  status: "draft"
};

const emptyContentForm: EpisodeContentForm = {
  detailed_content: "",
  key_beats: "",
  status: "draft"
};

const emptyScriptForm: EpisodeScriptForm = {
  scene_text: "",
  dialogue: "",
  action_notes: "",
  voiceover: "",
  status: "draft"
};

const emptyShotForm: ShotForm = {
  shot_no: "1",
  scene: "",
  visual_prompt: "",
  camera: "",
  duration_seconds: "",
  dialogue_or_voiceover: "",
  status: "draft"
};

const emptyCopyForm: CopywritingForm = {
  subtitles: "",
  platform_title: "",
  platform_description: "",
  publish_copy: "",
  status: "draft"
};

function projectToForm(project: ProjectSummary): ProjectForm {
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

function worldSnapshotToForm(snapshot: ProjectWorldSnapshot): WorldSnapshotForm {
  return {
    name: snapshot.name,
    genre: snapshot.genre,
    snapshot_content: snapshot.snapshot_content,
    entry_snapshot_content: snapshot.entry_snapshot_content
  };
}

function characterSnapshotToForm(snapshot: ProjectCharacterSnapshot): CharacterSnapshotForm {
  return {
    name: snapshot.name,
    gender: snapshot.gender,
    role_type: snapshot.role_type,
    snapshot_content: snapshot.snapshot_content,
    visual_description: snapshot.visual_description || "",
    reference_image_url: snapshot.reference_image_url || "",
    reference_local_path: snapshot.reference_local_path || ""
  };
}

function storyOutlineToForm(outline: ProjectStoryOutline | null): StoryOutlineForm {
  if (!outline) return emptyStoryForm;
  return {
    logline: outline.logline || "",
    core_conflict: outline.core_conflict || "",
    main_goal: outline.main_goal || "",
    character_arcs: outline.character_arcs || "",
    ending_direction: outline.ending_direction || "",
    notes: outline.notes || "",
    status: outline.status
  };
}

function episodeOutlineToForm(outline: ProjectEpisodeOutline | null): EpisodeOutlineForm {
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

function episodeContentToForm(content: ProjectEpisodeContent | null): EpisodeContentForm {
  if (!content) return emptyContentForm;
  return {
    detailed_content: content.detailed_content || "",
    key_beats: content.key_beats || "",
    status: content.status
  };
}

function episodeScriptToForm(script: ProjectEpisodeScript | null): EpisodeScriptForm {
  if (!script) return emptyScriptForm;
  return {
    scene_text: script.scene_text || "",
    dialogue: script.dialogue || "",
    action_notes: script.action_notes || "",
    voiceover: script.voiceover || "",
    status: script.status
  };
}

function shotToForm(shot: ProjectStoryboardShot): ShotForm {
  return {
    shot_no: String(shot.shot_no),
    scene: shot.scene || "",
    visual_prompt: shot.visual_prompt || "",
    camera: shot.camera || "",
    duration_seconds: shot.duration_seconds ? String(shot.duration_seconds) : "",
    dialogue_or_voiceover: shot.dialogue_or_voiceover || "",
    status: shot.status
  };
}

function copywritingToForm(copy: ProjectCopywriting | null): CopywritingForm {
  if (!copy) return emptyCopyForm;
  return {
    subtitles: copy.subtitles || "",
    platform_title: copy.platform_title || "",
    platform_description: copy.platform_description || "",
    publish_copy: copy.publish_copy || "",
    status: copy.status
  };
}

function validateProject(form: ProjectForm, episodeCount: number, episodeDuration: number, totalDuration: number) {
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
  if (totalDuration > 240) {
    return "总时长不能超过 240 分钟，请减少集数或单集时长";
  }
  return "";
}

function replaceEpisodeOutline(current: ProjectEpisodeOutline[], next: ProjectEpisodeOutline) {
  const filtered = current.filter((outline) => outline.episode_no !== next.episode_no);
  return [...filtered, next].sort((a, b) => a.episode_no - b.episode_no);
}

function replaceWorldSnapshot(current: ProjectWorldSnapshot[], next: ProjectWorldSnapshot) {
  const filtered = current.filter((snapshot) => snapshot.id !== next.id);
  return [...filtered, next].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
}

function replaceCharacterSnapshot(current: ProjectCharacterSnapshot[], next: ProjectCharacterSnapshot) {
  const filtered = current.filter((snapshot) => snapshot.id !== next.id);
  return [...filtered, next].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
}

function replaceShot(current: ProjectStoryboardShot[], next: ProjectStoryboardShot) {
  const filtered = current.filter((shot) => shot.id !== next.id);
  return [...filtered, next].sort((a, b) => a.shot_no - b.shot_no);
}

function nextShotNo(shots: ProjectStoryboardShot[]) {
  return shots.reduce((max, shot) => Math.max(max, shot.shot_no), 0) + 1;
}

function setProjectFormValue(field: keyof ProjectForm, value: string, setter: Dispatch<SetStateAction<ProjectForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

function setWorldSnapshotFormValue(field: keyof WorldSnapshotForm, value: string, setter: Dispatch<SetStateAction<WorldSnapshotForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

function setCharacterSnapshotFormValue(
  field: keyof CharacterSnapshotForm,
  value: string | "男" | "女",
  setter: Dispatch<SetStateAction<CharacterSnapshotForm>>
) {
  setter((current) => ({ ...current, [field]: value }));
}

function setStoryFormValue(field: keyof StoryOutlineForm, value: string | ProjectArtifactStatus, setter: Dispatch<SetStateAction<StoryOutlineForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

function setEpisodeFormValue(field: keyof EpisodeOutlineForm, value: string | ProjectArtifactStatus, setter: Dispatch<SetStateAction<EpisodeOutlineForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

function setContentFormValue(field: keyof EpisodeContentForm, value: string | ProjectArtifactStatus, setter: Dispatch<SetStateAction<EpisodeContentForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

function setScriptFormValue(field: keyof EpisodeScriptForm, value: string | ProjectArtifactStatus, setter: Dispatch<SetStateAction<EpisodeScriptForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

function setShotFormValue(field: keyof ShotForm, value: string | ProjectArtifactStatus, setter: Dispatch<SetStateAction<ShotForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

function setCopyFormValue(field: keyof CopywritingForm, value: string | ProjectArtifactStatus, setter: Dispatch<SetStateAction<CopywritingForm>>) {
  setter((current) => ({ ...current, [field]: value }));
}

function toOptional(value: string) {
  const stripped = value.trim();
  return stripped || undefined;
}

function toOptionalNumber(value: string) {
  if (!value.trim()) return undefined;
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : undefined;
}

function artifactStatusLabel(status: ProjectArtifactStatus) {
  if (status === "confirmed") return "已确认";
  if (status === "needs_review") return "需要检查";
  return "草稿";
}

function artifactStatusClass(status: ProjectArtifactStatus) {
  if (status === "confirmed") return "status-active";
  if (status === "needs_review") return "status-review";
  return "status-draft";
}

function worldSnapshotSummary(snapshot: ProjectWorldSnapshot) {
  const content = parseSnapshot(snapshot.snapshot_content);
  if (content && typeof content.summary === "string" && content.summary.trim()) {
    return content.summary;
  }
  if (content && typeof content.world_rules === "string" && content.world_rules.trim()) {
    return content.world_rules;
  }
  return "已加载到项目的世界观副本。";
}

function characterSnapshotSummary(snapshot: ProjectCharacterSnapshot) {
  const content = parseSnapshot(snapshot.snapshot_content);
  if (content && typeof content.identity === "string" && content.identity.trim()) {
    return content.identity;
  }
  if (content && typeof content.goal === "string" && content.goal.trim()) {
    return content.goal;
  }
  return "已加载到项目的角色副本。";
}

function parseSnapshot(content: string): Record<string, unknown> | null {
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

function formatNumber(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}
