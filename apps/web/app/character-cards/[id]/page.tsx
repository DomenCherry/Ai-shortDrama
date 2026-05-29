"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  archiveCharacterCard,
  CharacterCard,
  confirmCharacterTurnaroundByVersion,
  generateCharacterTurnaround,
  getCharacterCard,
  listProjects,
  loadCharacterCardToProject,
  ProjectSummary,
  resolveAssetUrl,
  uploadCharacterReferenceImage,
  updateCharacterCard
} from "@/lib/api";
import {
  cardToForm,
  CharacterCardForm,
  CharacterCardFormView,
  emptyCharacterCardForm,
  formToPayload,
  statusLabel,
  validateCharacterCard
} from "../_components/CharacterCardForm";

export default function CharacterCardDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const cardId = Array.isArray(params.id) ? params.id[0] : params.id;
  const [card, setCard] = useState<CharacterCard | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [form, setForm] = useState<CharacterCardForm>(emptyCharacterCardForm);
  const [targetProjectId, setTargetProjectId] = useState("");
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isArchiving, setIsArchiving] = useState(false);
  const [isUploadingReference, setIsUploadingReference] = useState(false);
  const [isGeneratingTurnaround, setIsGeneratingTurnaround] = useState(false);
  const [isConfirmingTurnaround, setIsConfirmingTurnaround] = useState(false);
  const [isLoadingToProject, setIsLoadingToProject] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const validationError = validateCharacterCard(form);
  const isArchived = form.status === "archived";

  useEffect(() => {
    void loadInitialData();
  }, [cardId]);

  const loadInitialData = async () => {
    setIsLoading(true);
    setError("");
    try {
      const [cardDetail, projectList] = await Promise.all([getCharacterCard(cardId), listProjects()]);
      setCard(cardDetail);
      setForm(cardToForm(cardDetail));
      setProjects(projectList);
      setTargetProjectId(projectList[0]?.id ?? "");
      setHasUnsavedChanges(false);
      applyRouteFeedback(setStatusMessage, setError);
    } catch (err) {
      setError(err instanceof Error ? err.message : "角色卡详情加载失败");
    } finally {
      setIsLoading(false);
    }
  };

  const updateField = (field: keyof CharacterCardForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    setHasUnsavedChanges(true);
  };

  const saveCard = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setStatusMessage("");

    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSaving(true);
    try {
      const savedCard = await updateCharacterCard(cardId, formToPayload(form));
      setCard(savedCard);
      setForm(cardToForm(savedCard));
      setHasUnsavedChanges(false);
      setStatusMessage("角色卡已保存。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "角色卡保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const setActiveAndSave = () => {
    setForm((current) => ({ ...current, status: "active" }));
    setHasUnsavedChanges(true);
    setStatusMessage("已切换为可加载，请保存后再加载到项目。");
  };

  const archiveCard = async () => {
    if (!window.confirm("归档后，该角色卡不再作为新项目可选项。确认归档？")) {
      return;
    }

    setIsArchiving(true);
    setError("");
    setStatusMessage("");
    try {
      const archived = await archiveCharacterCard(cardId);
      setCard(archived);
      setForm(cardToForm(archived));
      setHasUnsavedChanges(false);
      setStatusMessage("角色卡已归档。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "角色卡归档失败");
    } finally {
      setIsArchiving(false);
    }
  };

  const loadToProject = async () => {
    if (hasUnsavedChanges) {
      setError("当前角色卡有未保存修改，请先保存后再加载到项目。");
      return;
    }
    if (form.status !== "active") {
      setError("只有可加载状态的角色卡可以加入项目。");
      return;
    }
    if (!targetProjectId) {
      setError("请先选择要加载到的项目。");
      return;
    }

    setIsLoadingToProject(true);
    setError("");
    setStatusMessage("");
    try {
      // 加载到项目时只创建项目内快照，项目后续修改不会回写角色卡库原始内容。
      await loadCharacterCardToProject(targetProjectId, cardId);
      setStatusMessage("角色卡已加载到项目，项目内将使用独立快照。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "角色卡加载失败");
    } finally {
      setIsLoadingToProject(false);
    }
  };

  const uploadReferenceImage = async (file: File | null) => {
    if (!file) return;
    if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) {
      setError("请上传 png、jpg 或 webp 格式图片。");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("参考图不能超过 10MB。");
      return;
    }

    setIsUploadingReference(true);
    setError("");
    setStatusMessage("");
    try {
      const dataUrl = await readFileAsDataUrl(file);
      const uploaded = await uploadCharacterReferenceImage(cardId, {
        filename: file.name,
        content_type: file.type,
        data_url: dataUrl
      });
      setForm((current) => ({
        ...current,
        reference_image_url: uploaded.image_url,
        reference_local_path: uploaded.local_path
      }));
      setCard((current) =>
        current
          ? {
              ...current,
              reference_image_url: uploaded.image_url,
              reference_local_path: uploaded.local_path,
              updated_at: uploaded.updated_at
            }
          : current
      );
      setStatusMessage("参考图已上传。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "参考图上传失败，请稍后重试。");
    } finally {
      setIsUploadingReference(false);
    }
  };

  const generateTurnaround = async () => {
    if (hasUnsavedChanges) {
      setError("请先保存角色卡，再生成人物三视图。");
      return;
    }
    if (!form.name.trim() || !form.gender || !form.identity.trim() || !form.goal.trim()) {
      setError("请先填写角色名、性别、身份摘要和人物目标后再生成三视图。");
      return;
    }
    if (!form.visual_description.trim() && !form.image_keywords.trim()) {
      setError("请先填写视觉描述或形象关键词后再生成三视图。");
      return;
    }

    setIsGeneratingTurnaround(true);
    setError("");
    setStatusMessage("");
    try {
      const result = await generateCharacterTurnaround(cardId, form.turnaround_prompt);
      setCard((current) =>
        current
          ? {
              ...current,
              turnaround_image_url: result.image_url,
              turnaround_local_path: result.local_path,
              turnaround_generation_prompt: result.generation_prompt,
              turnaround_status: result.status,
              turnaround_version: result.version,
              turnaround_confirmed_at: result.confirmed_at,
              updated_at: result.updated_at
            }
          : current
      );
      setStatusMessage("人物三视图已生成，请确认后作为视觉参考素材。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "三视图生成失败，请稍后重试。");
    } finally {
      setIsGeneratingTurnaround(false);
    }
  };

  const confirmTurnaround = async () => {
    if (!card) return;
    setIsConfirmingTurnaround(true);
    setError("");
    setStatusMessage("");
    try {
      const result = await confirmCharacterTurnaroundByVersion(cardId, card.turnaround_version);
      setCard((current) =>
        current
          ? {
              ...current,
              turnaround_status: result.status,
              turnaround_confirmed_at: result.confirmed_at,
              updated_at: result.updated_at
            }
          : current
      );
      setStatusMessage("人物三视图已确认，将作为后续视频生成的角色视觉参考。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "三视图确认失败，请稍后重试。");
    } finally {
      setIsConfirmingTurnaround(false);
    }
  };

  const leaveToList = () => {
    if (hasUnsavedChanges && !window.confirm("当前页面有未保存内容，确认离开吗？")) {
      return;
    }
    router.push("/character-cards");
  };

  if (isLoading) {
    return <div className="panel">角色卡详情加载中...</div>;
  }

  if (!card) {
    return (
      <div className="stack">
        <div className="error">{error || "角色卡详情加载失败"}</div>
        <Link className="button secondary" href="/character-cards">
          返回列表
        </Link>
      </div>
    );
  }

  return (
    <div className="stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">{card.name}</h1>
          <p className="page-description">维护角色卡完整设定，并在需要时加载到短剧项目生成独立角色快照。</p>
        </div>
        <button className="button secondary" type="button" onClick={leaveToList}>
          返回列表
        </button>
      </header>

      <form className="grid-2 detail-layout" onSubmit={saveCard}>
        <main className="panel stack">
          <div className="section-heading">
            <h2>角色设定</h2>
            <div className="meta-line">
              <span className={`status-badge status-${form.status}`}>{statusLabel(form.status)}</span>
              <span>v{card.version}</span>
              {hasUnsavedChanges ? <span className="warning-text">有未保存修改</span> : null}
            </div>
          </div>

          {isArchived ? <div className="warning-text">当前角色已归档，不再作为新项目加载候选。</div> : null}

          <CharacterCardFormView form={form} onChange={updateField} disabled={isArchived} />

          <section className="form-section stack">
            <h3>参考图上传</h3>
            <p className="field-hint">上传人物氛围图、服装参考或脸部风格参考。该图片会作为三视图生成输入，不需要手动填写本地路径。</p>
            <div className="grid-2">
              <div className="field">
                <label>上传参考图</label>
                <input
                  accept="image/png,image/jpeg,image/webp"
                  disabled={isArchived || isUploadingReference}
                  type="file"
                  onChange={(event) => void uploadReferenceImage(event.target.files?.[0] ?? null)}
                />
                <span className="field-hint">支持 png、jpg、webp，单张不超过 10MB。</span>
              </div>
              <div className="reference-preview compact-preview">
                {form.reference_image_url ? (
                  <img src={resolveAssetUrl(form.reference_image_url)} alt="角色参考图预览" />
                ) : (
                  <div className="image-placeholder">暂未上传参考图。</div>
                )}
              </div>
            </div>
            {isUploadingReference ? <div className="hint">参考图上传中...</div> : null}
          </section>

          <section className="form-section stack">
            <h3>人物三视图</h3>
            <p className="field-hint">
              系统会合并角色名、性别、身份、目标、背景、口吻、视觉描述、形象关键词、三视图提示词和参考图信息调用图片生成接口。
            </p>
            <div className="turnaround-preview">
              {card.turnaround_image_url ? (
                <img src={resolveAssetUrl(card.turnaround_image_url)} alt="人物三视图预览" />
              ) : (
                <div className="image-placeholder">尚未生成人物三视图。</div>
              )}
            </div>
            <div className="meta-line">
              <span className={`status-badge status-${card.turnaround_status === "confirmed" ? "active" : "draft"}`}>
                {turnaroundStatusLabel(card.turnaround_status)}
              </span>
              <span>三视图版本 v{card.turnaround_version}</span>
            </div>
            <div className="actions action-wrap">
              <button
                className="button secondary"
                disabled={isArchived || isGeneratingTurnaround || hasUnsavedChanges}
                type="button"
                onClick={generateTurnaround}
              >
                {isGeneratingTurnaround ? "生成中..." : "生成人物三视图"}
              </button>
              <button
                className="button"
                disabled={isArchived || isConfirmingTurnaround || !card.turnaround_image_url || card.turnaround_status === "confirmed"}
                type="button"
                onClick={confirmTurnaround}
              >
                {isConfirmingTurnaround ? "确认中..." : "确认三视图"}
              </button>
            </div>
          </section>

          {validationError ? <div className="error">{validationError}</div> : null}
          {error ? <div className="error">{error}</div> : null}
          {statusMessage ? <div className="success">{statusMessage}</div> : null}

          <div className="actions action-wrap">
            <button className="button secondary" type="button" onClick={setActiveAndSave} disabled={isArchived}>
              设为可加载
            </button>
            <button className="button danger" type="button" onClick={archiveCard} disabled={isArchived || isArchiving}>
              {isArchiving ? "归档中..." : "归档"}
            </button>
            <button className="button" type="submit" disabled={isArchived || isSaving || Boolean(validationError)}>
              {isSaving ? "保存中..." : "保存角色卡"}
            </button>
          </div>
        </main>

        <aside className="panel stack side-panel">
          <section className="stack">
            <h2>加载到项目</h2>
            <div className="field">
              <label>目标项目</label>
              <select value={targetProjectId} onChange={(event) => setTargetProjectId(event.target.value)}>
                {projects.length === 0 ? <option value="">暂无项目</option> : null}
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.title}
                  </option>
                ))}
              </select>
            </div>
            <div className="summary-box">角色卡会复制为项目内快照，项目内修改不会影响原始角色卡。</div>
            <button
              className="button"
              type="button"
              onClick={loadToProject}
              disabled={form.status !== "active" || hasUnsavedChanges || isLoadingToProject}
            >
              {isLoadingToProject ? "加载中..." : "加载到项目"}
            </button>
          </section>

          <section className="stack">
            <h2>角色信息</h2>
            <div className="summary-box">
              <p>创建时间：{new Date(card.created_at).toLocaleString()}</p>
              <p>更新时间：{new Date(card.updated_at).toLocaleString()}</p>
              <p>参考图：{card.reference_image_url ? "已设置" : "未设置"}</p>
            </div>
          </section>
        </aside>
      </form>
    </div>
  );
}

function readFileAsDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("参考图读取失败，请重新选择文件。"));
    reader.readAsDataURL(file);
  });
}

function turnaroundStatusLabel(status: CharacterCard["turnaround_status"]) {
  if (status === "confirmed") return "已确认";
  if (status === "generated") return "待确认";
  if (status === "failed") return "生成失败";
  return "未生成";
}

function applyRouteFeedback(
  setStatusMessage: (message: string) => void,
  setError: (message: string) => void
) {
  const searchParams = new URLSearchParams(window.location.search);
  const error = searchParams.get("error");
  if (error) {
    setError(error);
    return;
  }

  const notice = searchParams.get("notice");
  if (notice === "reference_uploaded") {
    setStatusMessage("参考图已上传。");
  }
  if (notice === "turnaround_generated") {
    setStatusMessage("人物三视图已生成，请确认后作为视觉参考素材。");
  }
}
