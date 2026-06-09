"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SimpleSelect } from "@/components/ui/simple-select";
import { Textarea } from "@/components/ui/textarea";
import {
  archiveWorldBook,
  createWorldEntry,
  disableWorldEntry,
  enableWorldEntry,
  getWorldBook,
  listProjects,
  listWorldEntries,
  loadWorldBookToProject,
  ProjectSummary,
  updateWorldBook,
  updateWorldEntry,
  WorldBook,
  WorldEntry,
  WorldEntryPayload,
  WorldEntryStatus,
  WorldEntryType
} from "@/lib/api";
import {
  emptyWorldBookForm,
  formToPayload,
  validateWorldBook,
  WorldBookForm,
  WorldBookFormView,
  worldBookStatusLabel,
  worldBookToForm
} from "../_components/WorldBookForm";

type WorldEntryForm = {
  title: string;
  entry_type: WorldEntryType;
  keywords: string;
  content: string;
  applicable_scope: string;
  priority: string;
  status: WorldEntryStatus;
};

const entryTypes: WorldEntryType[] = ["世界规则", "地点", "组织", "阶层关系", "历史事件", "特殊物品", "禁忌或限制", "风格约束", "其他"];

const emptyEntryForm: WorldEntryForm = {
  title: "",
  entry_type: "世界规则",
  keywords: "",
  content: "",
  applicable_scope: "全局",
  priority: "0",
  status: "active"
};

export default function WorldBookDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const worldBookId = Array.isArray(params.id) ? params.id[0] : params.id;
  const [worldBook, setWorldBook] = useState<WorldBook | null>(null);
  const [entries, setEntries] = useState<WorldEntry[]>([]);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [form, setForm] = useState<WorldBookForm>(emptyWorldBookForm);
  const [entryForm, setEntryForm] = useState<WorldEntryForm>(emptyEntryForm);
  const [editingEntryId, setEditingEntryId] = useState("");
  const [targetProjectId, setTargetProjectId] = useState("");
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [entryError, setEntryError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isArchiving, setIsArchiving] = useState(false);
  const [isSavingEntry, setIsSavingEntry] = useState(false);
  const [isLoadingToProject, setIsLoadingToProject] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const validationError = validateWorldBook(form);
  const isArchived = form.status === "archived";

  useEffect(() => {
    void loadInitialData();
  }, [worldBookId]);

  const loadInitialData = async () => {
    setIsLoading(true);
    setError("");
    try {
      const [bookDetail, entryList, projectList] = await Promise.all([
        getWorldBook(worldBookId),
        listWorldEntries(worldBookId),
        listProjects()
      ]);
      setWorldBook(bookDetail);
      setEntries(entryList);
      setProjects(projectList);
      setTargetProjectId(projectList[0]?.id ?? "");
      setForm(worldBookToForm(bookDetail));
      setHasUnsavedChanges(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "世界观详情加载失败");
    } finally {
      setIsLoading(false);
    }
  };

  const refreshWorldBookAndEntries = async () => {
    const [bookDetail, entryList] = await Promise.all([getWorldBook(worldBookId), listWorldEntries(worldBookId)]);
    setWorldBook(bookDetail);
    setForm(worldBookToForm(bookDetail));
    setEntries(entryList);
    setHasUnsavedChanges(false);
  };

  const updateField = (field: keyof WorldBookForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    setHasUnsavedChanges(true);
  };

  const updateEntryField = (field: keyof WorldEntryForm, value: string) => {
    setEntryForm((current) => ({ ...current, [field]: value }));
    setEntryError("");
  };

  const saveWorldBook = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setStatusMessage("");

    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSaving(true);
    try {
      const saved = await updateWorldBook(worldBookId, formToPayload(form));
      setWorldBook(saved);
      setForm(worldBookToForm(saved));
      setHasUnsavedChanges(false);
      setStatusMessage("世界观已保存。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "世界观保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const setActiveAndSave = () => {
    setForm((current) => ({ ...current, status: "active" }));
    setHasUnsavedChanges(true);
    setStatusMessage("已切换为可加载，请保存后再加载到项目。");
  };

  const archiveBook = async () => {
    if (!window.confirm("归档后，该世界观不再作为新项目可选项。确认归档？")) {
      return;
    }

    setIsArchiving(true);
    setError("");
    setStatusMessage("");
    try {
      const archived = await archiveWorldBook(worldBookId);
      setWorldBook(archived);
      setForm(worldBookToForm(archived));
      setHasUnsavedChanges(false);
      setStatusMessage("世界观已归档。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "世界观归档失败");
    } finally {
      setIsArchiving(false);
    }
  };

  const saveEntry = async () => {
    const entryValidationError = validateWorldEntry(entryForm);
    if (entryValidationError) {
      setEntryError(entryValidationError);
      return;
    }

    setIsSavingEntry(true);
    setEntryError("");
    setStatusMessage("");
    try {
      if (editingEntryId) {
        await updateWorldEntry(worldBookId, editingEntryId, entryFormToPayload(entryForm));
        setStatusMessage("世界观条目已保存。");
      } else {
        await createWorldEntry(worldBookId, entryFormToPayload(entryForm));
        setStatusMessage("世界观条目已新增。");
      }
      setEntryForm(emptyEntryForm);
      setEditingEntryId("");
      await refreshWorldBookAndEntries();
    } catch (err) {
      setEntryError(err instanceof Error ? err.message : "世界观条目保存失败");
    } finally {
      setIsSavingEntry(false);
    }
  };

  const editEntry = (entry: WorldEntry) => {
    setEditingEntryId(entry.id);
    setEntryForm(entryToForm(entry));
    setEntryError("");
  };

  const cancelEntryEdit = () => {
    setEditingEntryId("");
    setEntryForm(emptyEntryForm);
    setEntryError("");
  };

  const toggleEntryStatus = async (entry: WorldEntry) => {
    setEntryError("");
    setStatusMessage("");
    try {
      if (entry.status === "active") {
        await disableWorldEntry(worldBookId, entry.id);
        setStatusMessage("世界观条目已停用。");
      } else {
        await enableWorldEntry(worldBookId, entry.id);
        setStatusMessage("世界观条目已启用。");
      }
      await refreshWorldBookAndEntries();
    } catch (err) {
      setEntryError(err instanceof Error ? err.message : "世界观条目状态更新失败");
    }
  };

  const loadToProject = async () => {
    if (hasUnsavedChanges) {
      setError("当前世界观有未保存修改，请先保存后再加载到项目。");
      return;
    }
    if (form.status !== "active") {
      setError("只有可加载状态的世界观可以加入项目。");
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
      await loadWorldBookToProject(targetProjectId, worldBookId);
      setStatusMessage("世界观已加载到项目，项目内将使用独立快照。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "世界观加载失败");
    } finally {
      setIsLoadingToProject(false);
    }
  };

  const leaveToList = () => {
    if (hasUnsavedChanges && !window.confirm("当前页面有未保存内容，确认离开吗？")) {
      return;
    }
    router.push("/world-books");
  };

  if (isLoading) {
    return <div className="panel">世界观详情加载中...</div>;
  }

  if (!worldBook) {
    return (
      <div className="stack">
        <div className="error">{error || "世界观详情加载失败"}</div>
        <Button className="button secondary" asChild>
          <Link href="/world-books">返回列表</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">{worldBook.name}</h1>
          <p className="page-description">维护世界观基础设定和结构化条目，并在需要时加载到短剧项目生成独立快照。</p>
        </div>
        <Button className="button secondary" type="button" onClick={leaveToList}>
          返回列表
        </Button>
      </header>

      <form className="grid-2 detail-layout" onSubmit={saveWorldBook}>
        <main className="panel stack">
          <div className="section-heading">
            <h2>世界观设定</h2>
            <div className="meta-line">
              <Badge className={`status-badge status-${form.status}`}>{worldBookStatusLabel(form.status)}</Badge>
              <span>v{worldBook.version}</span>
              {hasUnsavedChanges ? <span className="warning-text">有未保存修改</span> : null}
            </div>
          </div>

          {isArchived ? <div className="warning-text">当前世界观已归档，不再作为新项目加载候选。</div> : null}

          <WorldBookFormView form={form} onChange={updateField} disabled={isArchived} />

          <section className="form-section stack">
            <h3>世界观条目</h3>
            <div className="grid-2">
              <InputField label="条目标题" value={entryForm.title} disabled={isArchived} onChange={(value) => updateEntryField("title", value)} placeholder="例如：雾港登记法、沈氏顶层会议室" />
              <div className="field">
                <label>条目类型</label>
                <SimpleSelect
                  disabled={isArchived}
                  value={entryForm.entry_type}
                  onValueChange={(value) => updateEntryField("entry_type", value)}
                  options={entryTypes.map((entryType) => ({ label: entryType, value: entryType }))}
                />
              </div>
              <InputField label="关键词" value={entryForm.keywords} disabled={isArchived} onChange={(value) => updateEntryField("keywords", value)} placeholder="例如：登记法、异能者、调查局" />
              <InputField label="适用范围" value={entryForm.applicable_scope} disabled={isArchived} onChange={(value) => updateEntryField("applicable_scope", value)} placeholder="例如：全局、女主线、第三幕" />
              <InputField label="优先级" value={entryForm.priority} disabled={isArchived} onChange={(value) => updateEntryField("priority", value)} placeholder="数字越大越优先" type="number" />
              <div className="field">
                <label>条目状态</label>
                <SimpleSelect
                  disabled={isArchived}
                  value={entryForm.status}
                  onValueChange={(value) => updateEntryField("status", value)}
                  options={[
                    { label: "启用", value: "active" },
                    { label: "停用", value: "disabled" }
                  ]}
                />
              </div>
            </div>
            <div className="field">
              <label>条目正文</label>
              <Textarea
                disabled={isArchived}
                value={entryForm.content}
                onChange={(event) => updateEntryField("content", event.target.value)}
                placeholder="写清这个条目在生成故事、人物、分集或剧本时必须参考的设定。"
              />
            </div>
            {entryError ? <div className="error">{entryError}</div> : null}
            <div className="actions action-wrap">
              {editingEntryId ? (
                <Button className="button secondary" type="button" onClick={cancelEntryEdit}>
                  取消编辑
                </Button>
              ) : null}
              <Button className="button secondary" type="button" onClick={saveEntry} disabled={isArchived || isSavingEntry}>
                {isSavingEntry ? "保存中..." : editingEntryId ? "保存条目" : "新增条目"}
              </Button>
            </div>

            <div className="asset-list world-entry-list">
              {entries.length === 0 ? <div className="empty-state">还没有世界观条目。可以先把核心规则、组织、地点和禁忌拆成可引用条目。</div> : null}
              {entries.map((entry) => (
                <article className="asset-card" key={entry.id}>
                  <div className="asset-card-title">
                    <strong>{entry.title}</strong>
                    <Badge className={`status-badge status-${entry.status === "active" ? "active" : "archived"}`}>
                      {entry.status === "active" ? "启用" : "停用"}
                    </Badge>
                  </div>
                  <div className="hint">
                    {entry.entry_type} · 优先级 {entry.priority} · {entry.applicable_scope || "全局"} ·{" "}
                    {new Date(entry.updated_at).toLocaleString()}
                  </div>
                  {entry.keywords ? <p className="hint">关键词：{entry.keywords}</p> : null}
                  <p>{entry.content}</p>
                  <div className="asset-card-actions">
                    <Button className="button secondary" type="button" onClick={() => editEntry(entry)} disabled={isArchived}>
                      编辑
                    </Button>
                    <Button className="button secondary" type="button" onClick={() => void toggleEntryStatus(entry)} disabled={isArchived}>
                      {entry.status === "active" ? "停用" : "启用"}
                    </Button>
                  </div>
                </article>
              ))}
            </div>
          </section>

          {validationError ? <div className="error">{validationError}</div> : null}
          {error ? <div className="error">{error}</div> : null}
          {statusMessage ? <div className="success">{statusMessage}</div> : null}

          <div className="actions action-wrap">
            <Button className="button secondary" type="button" onClick={setActiveAndSave} disabled={isArchived}>
              设为可加载
            </Button>
            <Button className="button danger" type="button" onClick={archiveBook} disabled={isArchived || isArchiving}>
              {isArchiving ? "归档中..." : "归档"}
            </Button>
            <Button className="button" type="submit" disabled={isArchived || isSaving || Boolean(validationError)}>
              {isSaving ? "保存中..." : "保存世界观"}
            </Button>
          </div>
        </main>

        <aside className="panel stack side-panel">
          <section className="stack">
            <h2>加载到项目</h2>
            <div className="field">
              <label>目标项目</label>
              <SimpleSelect
                value={targetProjectId}
                onValueChange={setTargetProjectId}
                options={
                  projects.length === 0
                    ? [{ label: "暂无项目", value: "" }]
                    : projects.map((project) => ({ label: project.title, value: project.id }))
                }
              />
            </div>
            <div className="summary-box">世界观会复制为项目内快照，只包含当前基础信息和启用条目。</div>
            <Button
              className="button"
              type="button"
              onClick={loadToProject}
              disabled={form.status !== "active" || hasUnsavedChanges || isLoadingToProject}
            >
              {isLoadingToProject ? "加载中..." : "加载到项目"}
            </Button>
          </section>

          <section className="stack">
            <h2>世界观信息</h2>
            <div className="summary-box">
              <p>创建时间：{new Date(worldBook.created_at).toLocaleString()}</p>
              <p>更新时间：{new Date(worldBook.updated_at).toLocaleString()}</p>
              <p>
                条目：{worldBook.active_entry_count}/{worldBook.entry_count} 个启用
              </p>
            </div>
          </section>
        </aside>
      </form>
    </div>
  );
}

function InputField({
  label,
  value,
  onChange,
  disabled,
  placeholder,
  type = "text"
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      <Input disabled={disabled} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} type={type} />
    </div>
  );
}

function validateWorldEntry(form: WorldEntryForm) {
  if (!form.title.trim()) {
    return "条目标题不能为空。";
  }
  if (!form.content.trim()) {
    return "条目正文不能为空。";
  }
  if (!Number.isFinite(Number(form.priority))) {
    return "优先级必须是数字。";
  }
  return "";
}

function entryFormToPayload(form: WorldEntryForm): WorldEntryPayload {
  return {
    title: form.title,
    entry_type: form.entry_type,
    keywords: optionalText(form.keywords),
    content: form.content,
    applicable_scope: optionalText(form.applicable_scope),
    priority: Number(form.priority),
    status: form.status
  };
}

function entryToForm(entry: WorldEntry): WorldEntryForm {
  return {
    title: entry.title ?? "",
    entry_type: entry.entry_type,
    keywords: entry.keywords ?? "",
    content: entry.content ?? "",
    applicable_scope: entry.applicable_scope ?? "全局",
    priority: String(entry.priority ?? 0),
    status: entry.status
  };
}

function optionalText(value: string) {
  return value.trim() || undefined;
}
