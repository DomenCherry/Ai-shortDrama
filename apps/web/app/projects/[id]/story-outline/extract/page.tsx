"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  extractReferenceStoryStructure,
  getProject,
  ProjectArtifactStatus,
  ProjectStoryOutlinePayload,
  ProjectSummary,
  ReferenceStoryStructureDraft,
  updateProjectStoryOutline
} from "@/lib/api";

type ReferenceStoryInputForm = {
  source_text: string;
  source_filename: string;
  user_requirements: string;
};

type StoryOutlineForm = {
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

const emptyReferenceInputForm: ReferenceStoryInputForm = {
  source_text: "",
  source_filename: "",
  user_requirements: ""
};

const emptyStoryForm: StoryOutlineForm = {
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

export default function StoryOutlineExtractPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const projectId = params.id;
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [referenceInputForm, setReferenceInputForm] = useState<ReferenceStoryInputForm>(emptyReferenceInputForm);
  const [previewForm, setPreviewForm] = useState<StoryOutlineForm>(emptyStoryForm);
  const [draft, setDraft] = useState<ReferenceStoryStructureDraft | null>(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [isLoadingProject, setIsLoadingProject] = useState(true);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let active = true;
    setIsLoadingProject(true);
    getProject(projectId)
      .then((result) => {
        if (active) setProject(result);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "项目资料加载失败");
      })
      .finally(() => {
        if (active) setIsLoadingProject(false);
      });
    return () => {
      active = false;
    };
  }, [projectId]);

  const handleReferenceFileChange = async (file: File | null) => {
    setError("");
    setStatus("");
    if (!file) return;
    const lowerName = file.name.toLowerCase();
    if (!lowerName.endsWith(".txt") && !lowerName.endsWith(".md")) {
      setError("第一版只支持上传 .txt 或 .md 文本文件。");
      return;
    }
    const text = await file.text();
    setReferenceInputForm((current) => ({
      ...current,
      source_filename: file.name,
      source_text: text
    }));
    setDraft(null);
    setPreviewForm(emptyStoryForm);
  };

  const extractStoryOutline = async () => {
    if (!referenceInputForm.source_text.trim()) {
      setError("请先上传或粘贴参考故事文本。");
      return;
    }
    setIsExtracting(true);
    setError("");
    setStatus("");
    setDraft(null);
    setPreviewForm(emptyStoryForm);
    try {
      const result = await extractReferenceStoryStructure(projectId, {
        source_type: referenceInputForm.source_filename ? "uploaded" : "pasted",
        source_filename: toOptional(referenceInputForm.source_filename),
        source_text: referenceInputForm.source_text,
        user_requirements: toOptional(referenceInputForm.user_requirements)
      });
      setDraft(result);
      setPreviewForm(storyPayloadToForm(result.outline_preview));
      setStatus(result.validation_status === "passed" ? "AI 提取已完成，可调整预览后确认。" : "AI 提取已完成，但未通过去具体化校验，不能确认写入。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI 提取失败");
    } finally {
      setIsExtracting(false);
    }
  };

  const confirmStoryOutline = async (event: FormEvent) => {
    event.preventDefault();
    if (!draft) {
      setError("请先完成 AI 提取。");
      return;
    }
    if (draft.validation_status !== "passed") {
      setError("抽取结果未通过去具体化校验，不能写入正式故事大纲。");
      return;
    }
    setIsSaving(true);
    setError("");
    setStatus("");
    try {
      await updateProjectStoryOutline(projectId, storyFormToPayload(previewForm));
      router.push(`/projects/${projectId}?stage=story`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "故事大纲确认失败");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">AI 提取故事大纲</h1>
          <p className="page-description">
            {isLoadingProject ? "正在加载项目资料..." : `${project?.title ?? "项目"} · 上传参考故事后抽取去具体化的大纲预览。`}
          </p>
        </div>
        <Link className="button secondary" href={`/projects/${projectId}?stage=story`}>
          返回故事大纲
        </Link>
      </header>

      {error ? <div className="error">{error}</div> : null}
      {status ? <div className="success">{status}</div> : null}

      <section className="panel stack">
        <div className="section-heading">
          <h2>参考故事输入</h2>
          {draft ? (
            <span className={`status-badge ${draft.validation_status === "passed" ? "status-active" : "status-review"}`}>
              {referenceValidationLabel(draft.validation_status)}
            </span>
          ) : null}
        </div>
        <div className="field">
          <label>上传参考故事（txt / md）</label>
          <input type="file" accept=".txt,.md,text/plain,text/markdown" onChange={(event) => void handleReferenceFileChange(event.target.files?.[0] ?? null)} />
        </div>
        {referenceInputForm.source_filename ? <div className="hint">已选择：{referenceInputForm.source_filename}</div> : null}
        <TextArea label="参考故事文本" value={referenceInputForm.source_text} onChange={(value) => updateReferenceInput({ source_text: value, source_filename: "" }, setReferenceInputForm, setDraft, setPreviewForm, setStatus)} />
        <TextArea label="抽取补充要求" value={referenceInputForm.user_requirements} onChange={(value) => updateReferenceInput({ user_requirements: value }, setReferenceInputForm, setDraft, setPreviewForm, setStatus)} />
        <div className="actions">
          <button className="button secondary" type="button" onClick={() => clearReferenceInput(setReferenceInputForm, setDraft, setPreviewForm, setStatus)} disabled={isExtracting}>
            清空
          </button>
          <button className="button" type="button" onClick={() => void extractStoryOutline()} disabled={isExtracting}>
            {isExtracting ? "提取中..." : "开始提取"}
          </button>
        </div>
        {draft?.validation_notes ? <div className="hint">{draft.validation_notes}</div> : null}
      </section>

      <section className="panel stack">
        <div className="section-heading">
          <h2>故事大纲预览</h2>
          <span className={`status-badge ${artifactStatusClass(previewForm.status)}`}>{artifactStatusLabel(previewForm.status)}</span>
        </div>
        <form className="stack" onSubmit={confirmStoryOutline}>
          <div className="grid-2">
            <TextArea label="一句话故事" value={previewForm.logline} onChange={(value) => setPreviewFormValue("logline", value, setPreviewForm)} />
            <TextArea label="故事背景" value={previewForm.story_background} onChange={(value) => setPreviewFormValue("story_background", value, setPreviewForm)} />
            <TextArea label="核心冲突" value={previewForm.core_conflict} onChange={(value) => setPreviewFormValue("core_conflict", value, setPreviewForm)} />
            <TextArea label="主线目标" value={previewForm.main_goal} onChange={(value) => setPreviewFormValue("main_goal", value, setPreviewForm)} />
            <TextArea label="故事起点" value={previewForm.story_start} onChange={(value) => setPreviewFormValue("story_start", value, setPreviewForm)} />
            <TextArea label="起承转合结构" value={previewForm.plot_structure} onChange={(value) => setPreviewFormValue("plot_structure", value, setPreviewForm)} />
            <TextArea label="阶段性反转" value={previewForm.reversals} onChange={(value) => setPreviewFormValue("reversals", value, setPreviewForm)} />
            <TextArea label="情绪曲线" value={previewForm.emotion_curve} onChange={(value) => setPreviewFormValue("emotion_curve", value, setPreviewForm)} />
            <TextArea label="关键伏笔" value={previewForm.foreshadowing} onChange={(value) => setPreviewFormValue("foreshadowing", value, setPreviewForm)} />
            <TextArea label="人物弧光" value={previewForm.character_arcs} onChange={(value) => setPreviewFormValue("character_arcs", value, setPreviewForm)} />
            <TextArea label="结局方向" value={previewForm.ending_direction} onChange={(value) => setPreviewFormValue("ending_direction", value, setPreviewForm)} />
            <TextArea label="整体节奏建议" value={previewForm.pacing_advice} onChange={(value) => setPreviewFormValue("pacing_advice", value, setPreviewForm)} />
            <TextArea label="剧情容量建议" value={previewForm.capacity_advice} onChange={(value) => setPreviewFormValue("capacity_advice", value, setPreviewForm)} />
            <TextArea label="补充说明" value={previewForm.notes} onChange={(value) => setPreviewFormValue("notes", value, setPreviewForm)} />
          </div>
          <StatusSelect value={previewForm.status} onChange={(value) => setPreviewFormValue("status", value, setPreviewForm)} />
          <div className="actions">
            <Link className="button secondary" href={`/projects/${projectId}?stage=story`}>
              取消
            </Link>
            <button className="button" type="submit" disabled={!draft || draft.validation_status !== "passed" || isSaving}>
              {isSaving ? "确认中..." : "确认并返回工作台"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function TextArea({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div className="field">
      <label>{label}</label>
      <textarea value={value} onChange={(event) => onChange(event.target.value)} rows={4} />
    </div>
  );
}

function StatusSelect({ value, onChange }: { value: ProjectArtifactStatus; onChange: (value: ProjectArtifactStatus) => void }) {
  return (
    <div className="field">
      <label>状态</label>
      <select value={value} onChange={(event) => onChange(event.target.value as ProjectArtifactStatus)}>
        <option value="draft">草稿</option>
        <option value="confirmed">已确认</option>
        <option value="needs_review">需要检查</option>
      </select>
    </div>
  );
}

function toOptional(value: string) {
  const stripped = value.trim();
  return stripped || undefined;
}

function storyPayloadToForm(payload: ProjectStoryOutlinePayload): StoryOutlineForm {
  return {
    logline: payload.logline || "",
    story_background: payload.story_background || "",
    core_conflict: payload.core_conflict || "",
    main_goal: payload.main_goal || "",
    story_start: payload.story_start || "",
    plot_structure: payload.plot_structure || "",
    reversals: payload.reversals || "",
    emotion_curve: payload.emotion_curve || "",
    foreshadowing: payload.foreshadowing || "",
    character_arcs: payload.character_arcs || "",
    ending_direction: payload.ending_direction || "",
    pacing_advice: payload.pacing_advice || "",
    capacity_advice: payload.capacity_advice || "",
    notes: payload.notes || "",
    status: payload.status
  };
}

function storyFormToPayload(form: StoryOutlineForm): ProjectStoryOutlinePayload {
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

function setPreviewFormValue(
  field: keyof StoryOutlineForm,
  value: string | ProjectArtifactStatus,
  setter: Dispatch<SetStateAction<StoryOutlineForm>>
) {
  setter((current) => ({ ...current, [field]: value }));
}

function updateReferenceInput(
  patch: Partial<ReferenceStoryInputForm>,
  setReferenceInputForm: Dispatch<SetStateAction<ReferenceStoryInputForm>>,
  setDraft: Dispatch<SetStateAction<ReferenceStoryStructureDraft | null>>,
  setPreviewForm: Dispatch<SetStateAction<StoryOutlineForm>>,
  setStatus: Dispatch<SetStateAction<string>>
) {
  setReferenceInputForm((current) => ({ ...current, ...patch }));
  setDraft(null);
  setPreviewForm(emptyStoryForm);
  setStatus("");
}

function clearReferenceInput(
  setReferenceInputForm: Dispatch<SetStateAction<ReferenceStoryInputForm>>,
  setDraft: Dispatch<SetStateAction<ReferenceStoryStructureDraft | null>>,
  setPreviewForm: Dispatch<SetStateAction<StoryOutlineForm>>,
  setStatus: Dispatch<SetStateAction<string>>
) {
  setReferenceInputForm(emptyReferenceInputForm);
  setDraft(null);
  setPreviewForm(emptyStoryForm);
  setStatus("");
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

function referenceValidationLabel(status: ReferenceStoryStructureDraft["validation_status"]) {
  if (status === "passed") return "校验通过";
  if (status === "failed") return "校验失败";
  return "校验中";
}
