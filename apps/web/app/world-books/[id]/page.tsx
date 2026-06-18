"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { SimpleSelect } from "@/components/ui/simple-select";
import { Skeleton } from "@/components/ui/skeleton";
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

type DetailTab = "settings" | "entries";
type EntryStatusFilter = "" | WorldEntryStatus;

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
  const [activeTab, setActiveTab] = useState<DetailTab>("settings");
  const [editingEntryId, setEditingEntryId] = useState("");
  const [selectedEntryId, setSelectedEntryId] = useState("");
  const [entrySearch, setEntrySearch] = useState("");
  const [entryTypeFilter, setEntryTypeFilter] = useState("");
  const [entryStatusFilter, setEntryStatusFilter] = useState<EntryStatusFilter>("");
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
  const [isArchiveConfirmOpen, setIsArchiveConfirmOpen] = useState(false);
  const [isLeaveConfirmOpen, setIsLeaveConfirmOpen] = useState(false);
  const validationError = validateWorldBook(form);
  const isArchived = form.status === "archived";
  const selectedEntry = entries.find((entry) => entry.id === selectedEntryId) ?? null;
  const filteredEntries = useMemo(() => {
    const keyword = entrySearch.trim().toLowerCase();

    return entries.filter((entry) => {
      const matchesType = entryTypeFilter ? entry.entry_type === entryTypeFilter : true;
      const matchesStatus = entryStatusFilter ? entry.status === entryStatusFilter : true;
      const matchesKeyword = keyword
        ? [entry.title, entry.keywords, entry.content, entry.applicable_scope].some((value) =>
            (value ?? "").toLowerCase().includes(keyword)
          )
        : true;

      return matchesType && matchesStatus && matchesKeyword;
    });
  }, [entries, entrySearch, entryStatusFilter, entryTypeFilter]);

  useEffect(() => {
    void loadInitialData();
  }, [worldBookId]);

  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("tab") === "entries") {
      setActiveTab("entries");
    }
  }, []);

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
      setSelectedEntryId(entryList[0]?.id ?? "");
      setEditingEntryId(entryList[0]?.id ?? "");
      setEntryForm(entryList[0] ? entryToForm(entryList[0]) : emptyEntryForm);
      setHasUnsavedChanges(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "世界观详情加载失败");
    } finally {
      setIsLoading(false);
    }
  };

  const refreshWorldBookAndEntries = async (focusEntryId?: string) => {
    const [bookDetail, entryList] = await Promise.all([getWorldBook(worldBookId), listWorldEntries(worldBookId)]);
    const nextEntry = entryList.find((entry) => entry.id === (focusEntryId ?? selectedEntryId)) ?? entryList[0] ?? null;
    setWorldBook(bookDetail);
    setForm(worldBookToForm(bookDetail));
    setEntries(entryList);
    setSelectedEntryId(nextEntry?.id ?? "");
    setEditingEntryId(nextEntry?.id ?? "");
    setEntryForm(nextEntry ? entryToForm(nextEntry) : emptyEntryForm);
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
      let savedEntry: WorldEntry;
      if (editingEntryId) {
        savedEntry = await updateWorldEntry(worldBookId, editingEntryId, entryFormToPayload(entryForm));
        setStatusMessage("世界观条目已保存。");
      } else {
        savedEntry = await createWorldEntry(worldBookId, entryFormToPayload(entryForm));
        setStatusMessage("世界观条目已新增。");
      }
      await refreshWorldBookAndEntries(savedEntry.id);
    } catch (err) {
      setEntryError(err instanceof Error ? err.message : "世界观条目保存失败");
    } finally {
      setIsSavingEntry(false);
    }
  };

  const selectEntry = (entry: WorldEntry) => {
    setActiveTab("entries");
    setSelectedEntryId(entry.id);
    setEditingEntryId(entry.id);
    setEntryForm(entryToForm(entry));
    setEntryError("");
  };

  const createEntryDraft = () => {
    setActiveTab("entries");
    setSelectedEntryId("");
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
      await refreshWorldBookAndEntries(entry.id);
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
    if (hasUnsavedChanges) {
      setIsLeaveConfirmOpen(true);
      return;
    }
    router.push("/world-books");
  };

  if (isLoading) {
    return (
      <div className="panel stack" aria-label="世界观详情加载中">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-80 max-w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (!worldBook) {
    return (
      <div className="stack">
        <div className="error">{error || "世界观详情加载失败"}</div>
        <Button variant="secondary" asChild>
          <Link href="/world-books">返回列表</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="stack">
      <ConfirmDialog
        destructive
        open={isArchiveConfirmOpen}
        title="归档世界观？"
        description="归档后，该世界观不再作为新项目可选项。已有项目快照不会被删除。"
        confirmLabel="归档"
        onOpenChange={setIsArchiveConfirmOpen}
        onConfirm={() => {
          setIsArchiveConfirmOpen(false);
          void archiveBook();
        }}
      />
      <ConfirmDialog
        open={isLeaveConfirmOpen}
        title="离开当前页面？"
        description="当前页面有未保存内容，离开后这些世界观修改不会保存。"
        confirmLabel="离开"
        onOpenChange={setIsLeaveConfirmOpen}
        onConfirm={() => {
          setIsLeaveConfirmOpen(false);
          router.push("/world-books");
        }}
      />
      <header className="page-header">
        <div>
          <h1 className="page-title">{worldBook.name}</h1>
          <p className="page-description">维护世界观基础设定和结构化条目，并在需要时加载到短剧项目生成独立快照。</p>
        </div>
        <Button variant="secondary" type="button" onClick={leaveToList}>
          返回列表
        </Button>
      </header>

      <section className="panel world-book-overview">
        <div className="world-book-overview-main">
          <div className="meta-line">
            <Badge className={`status-badge status-${form.status}`}>{worldBookStatusLabel(form.status)}</Badge>
            <span>v{worldBook.version}</span>
            <span>
              条目 {worldBook.active_entry_count}/{worldBook.entry_count} 个启用
            </span>
            {hasUnsavedChanges ? <span className="warning-text">有未保存修改</span> : null}
          </div>
          <p>{worldBook.summary || worldBook.era_background || "未填写摘要或时代背景。"}</p>
        </div>
        <div className="actions action-wrap world-book-overview-actions">
          <Button variant="secondary" type="button" onClick={() => setActiveTab("entries")}>
            查看条目
          </Button>
          <Button variant="secondary" type="button" onClick={createEntryDraft} disabled={isArchived}>
            新增条目
          </Button>
        </div>
      </section>

      <div className="grid-2 detail-layout">
        <main className="panel stack">
          <nav className="module-subnav asset-tab-nav" role="tablist" aria-label="世界观详情分类">
            <button
              aria-controls="world-book-settings-panel"
              aria-selected={activeTab === "settings"}
              className={`module-subnav-tab asset-tab-button ${activeTab === "settings" ? "active" : ""}`}
              id="world-book-settings-tab"
              role="tab"
              type="button"
              onClick={() => setActiveTab("settings")}
            >
              <span>基础设定</span>
            </button>
            <button
              aria-controls="world-book-entries-panel"
              aria-selected={activeTab === "entries"}
              className={`module-subnav-tab asset-tab-button ${activeTab === "entries" ? "active" : ""}`}
              id="world-book-entries-tab"
              role="tab"
              type="button"
              onClick={() => setActiveTab("entries")}
            >
              <span>条目库</span>
              <span className="asset-tab-count">{worldBook.entry_count}</span>
            </button>
          </nav>

          {error ? <div className="error">{error}</div> : null}
          {statusMessage ? <div className="success">{statusMessage}</div> : null}

          {activeTab === "settings" ? (
            <form
              aria-labelledby="world-book-settings-tab"
              className="asset-tab-panel stack"
              id="world-book-settings-panel"
              role="tabpanel"
              onSubmit={saveWorldBook}
            >
              <div className="section-heading">
                <h2>世界观设定</h2>
                <div className="meta-line">
                  <Badge className={`status-badge status-${form.status}`}>{worldBookStatusLabel(form.status)}</Badge>
                  <span>v{worldBook.version}</span>
                </div>
              </div>

              {isArchived ? <div className="warning-text">当前世界观已归档，不再作为新项目加载候选。</div> : null}

              <WorldBookFormView form={form} onChange={updateField} disabled={isArchived} />

              {validationError ? <div className="error">{validationError}</div> : null}

              <div className="actions action-wrap">
                <Button variant="secondary" type="button" onClick={setActiveAndSave} disabled={isArchived}>
                  设为可加载
                </Button>
                <Button variant="destructive" type="button" onClick={() => setIsArchiveConfirmOpen(true)} disabled={isArchived || isArchiving}>
                  {isArchiving ? "归档中..." : "归档"}
                </Button>
                <Button type="submit" disabled={isArchived || isSaving || Boolean(validationError)}>
                  {isSaving ? "保存中..." : "保存世界观"}
                </Button>
              </div>
            </form>
          ) : (
            <section
              aria-labelledby="world-book-entries-tab"
              className="asset-tab-panel stack"
              id="world-book-entries-panel"
              role="tabpanel"
            >
              <div className="section-heading">
                <div>
                  <h2>世界观条目</h2>
                  <p className="hint">将规则、地点、组织和限制拆成可检索条目，后续加载项目时只复制启用条目。</p>
                </div>
                <Button variant="secondary" type="button" onClick={createEntryDraft} disabled={isArchived}>
                  新增条目
                </Button>
              </div>

              <div className="world-entry-workspace">
                <aside className="world-entry-index stack" aria-label="世界观条目列表">
                  <div className="filter-bar world-entry-filter-bar">
                    <Input value={entrySearch} onChange={(event) => setEntrySearch(event.target.value)} placeholder="搜索标题、关键词或正文" />
                    <SimpleSelect
                      value={entryTypeFilter}
                      onValueChange={setEntryTypeFilter}
                      options={[{ label: "全部类型", value: "" }, ...entryTypes.map((entryType) => ({ label: entryType, value: entryType }))]}
                    />
                    <SimpleSelect
                      value={entryStatusFilter}
                      onValueChange={(value) => setEntryStatusFilter(value as EntryStatusFilter)}
                      options={[
                        { label: "全部状态", value: "" },
                        { label: "启用", value: "active" },
                        { label: "停用", value: "disabled" }
                      ]}
                    />
                  </div>

                  <div className="asset-list world-entry-list">
                    {entries.length === 0 ? (
                      <div className="empty-state">还没有世界观条目。可以先把核心规则、组织、地点和禁忌拆成可引用条目。</div>
                    ) : null}
                    {entries.length > 0 && filteredEntries.length === 0 ? <div className="empty-state">没有匹配当前筛选条件的条目。</div> : null}
                    {filteredEntries.map((entry) => (
                      <button
                        className={`asset-card world-entry-card ${entry.id === selectedEntryId ? "selected" : ""}`}
                        key={entry.id}
                        type="button"
                        onClick={() => selectEntry(entry)}
                      >
                        <div className="asset-card-title">
                          <strong>{entry.title}</strong>
                          <Badge className={`status-badge status-${entry.status === "active" ? "active" : "archived"}`}>
                            {entry.status === "active" ? "启用" : "停用"}
                          </Badge>
                        </div>
                        <div className="hint">
                          {entry.entry_type} · 优先级 {entry.priority} · {entry.applicable_scope || "全局"}
                        </div>
                        {entry.keywords ? <p className="hint">关键词：{entry.keywords}</p> : null}
                        <p className="world-entry-card-content">{entry.content}</p>
                      </button>
                    ))}
                  </div>
                </aside>

                <section className="world-entry-editor stack" aria-label={editingEntryId ? "编辑世界观条目" : "新增世界观条目"}>
                  <div className="section-heading">
                    <div>
                      <h3>{editingEntryId ? "编辑条目" : "新增条目"}</h3>
                      <p className="hint">
                        {editingEntryId && selectedEntry
                          ? `上次更新：${new Date(selectedEntry.updated_at).toLocaleString()}`
                          : "新条目保存后会进入左侧条目列表。"}
                      </p>
                    </div>
                    {selectedEntry ? (
                      <Badge className={`status-badge status-${selectedEntry.status === "active" ? "active" : "archived"}`}>
                        {selectedEntry.status === "active" ? "启用" : "停用"}
                      </Badge>
                    ) : null}
                  </div>

                  {isArchived ? <div className="warning-text">当前世界观已归档，条目只能查看不能编辑。</div> : null}

                  <div className="grid-2">
                    <InputField
                      label="条目标题"
                      value={entryForm.title}
                      disabled={isArchived}
                      onChange={(value) => updateEntryField("title", value)}
                      placeholder="例如：雾港登记法、沈氏顶层会议室"
                    />
                    <div className="field">
                      <label>条目类型</label>
                      <SimpleSelect
                        disabled={isArchived}
                        value={entryForm.entry_type}
                        onValueChange={(value) => updateEntryField("entry_type", value)}
                        options={entryTypes.map((entryType) => ({ label: entryType, value: entryType }))}
                      />
                    </div>
                    <InputField
                      label="关键词"
                      value={entryForm.keywords}
                      disabled={isArchived}
                      onChange={(value) => updateEntryField("keywords", value)}
                      placeholder="例如：登记法、异能者、调查局"
                    />
                    <InputField
                      label="适用范围"
                      value={entryForm.applicable_scope}
                      disabled={isArchived}
                      onChange={(value) => updateEntryField("applicable_scope", value)}
                      placeholder="例如：全局、女主线、第三幕"
                    />
                    <InputField
                      label="优先级"
                      value={entryForm.priority}
                      disabled={isArchived}
                      onChange={(value) => updateEntryField("priority", value)}
                      placeholder="数字越大越优先"
                      type="number"
                    />
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
                    {selectedEntry ? (
                      <Button variant="secondary" type="button" onClick={() => void toggleEntryStatus(selectedEntry)} disabled={isArchived}>
                        {selectedEntry.status === "active" ? "停用" : "启用"}
                      </Button>
                    ) : null}
                    <Button variant="secondary" type="button" onClick={saveEntry} disabled={isArchived || isSavingEntry}>
                      {isSavingEntry ? "保存中..." : editingEntryId ? "保存条目" : "新增条目"}
                    </Button>
                  </div>
                </section>
              </div>
            </section>
          )}
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
      </div>
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
