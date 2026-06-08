"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  assistProjectStoryOutline,
  getProject,
  getProjectStoryOutline,
  ProjectArtifactStatus,
  ProjectStoryOutlinePayload,
  ProjectSummary,
  StoryOutlineAssistCompletion,
  StoryOutlineAssistMessage,
  StoryOutlineAssistPatch,
  updateProjectStoryOutline
} from "@/lib/api";
import { storyOutlineFieldGroups, StoryOutlineField, StoryOutlineTextFieldKey } from "../../storyOutlineFields";

type StoryOutlineForm = Record<StoryOutlineTextFieldKey, string> & {
  status: ProjectArtifactStatus;
};

const storyOutlineTextFieldKeys = storyOutlineFieldGroups.flatMap((group) => group.fields.map((field) => field.key));
const requiredAssistFieldKeys = storyOutlineFieldGroups
  .filter((group) => group.id !== "execution")
  .flatMap((group) => group.fields.map((field) => field.key));
const fieldLabels = Object.fromEntries(storyOutlineFieldGroups.flatMap((group) => group.fields.map((field) => [field.key, field.label])));

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

export default function StoryOutlineAssistPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const projectId = params.id;
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [assistForm, setAssistForm] = useState<StoryOutlineForm>(emptyStoryForm);
  const [messages, setMessages] = useState<StoryOutlineAssistMessage[]>([]);
  const [fieldNotes, setFieldNotes] = useState<Record<string, string>>({});
  const [lastChangedFields, setLastChangedFields] = useState<StoryOutlineTextFieldKey[]>([]);
  const [replyText, setReplyText] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const completion = useMemo(() => computeCompletion(assistForm), [assistForm]);

  useEffect(() => {
    let active = true;
    async function loadAndStart() {
      setIsLoading(true);
      setError("");
      setStatus("");
      try {
        const [projectResult, outline] = await Promise.all([getProject(projectId), getProjectStoryOutline(projectId)]);
        if (!active) return;
        const initialForm = storyPayloadToForm(outline ?? emptyStoryForm);
        setProject(projectResult);
        setAssistForm(initialForm);
        const result = await assistProjectStoryOutline(projectId, {
          action: "start",
          current_outline: storyFormToPayload(initialForm),
          messages: [],
          user_message: undefined
        });
        if (!active) return;
        setMessages([{ role: "assistant", content: result.assistant_message }]);
        setFieldNotes(result.field_notes ?? {});
        const changedFields = changedPatchFields(initialForm, result.outline_patch);
        setLastChangedFields(changedFields);
        setAssistForm((current) => mergePatchIntoForm(current, result.outline_patch));
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "AI 协助初始化失败");
      } finally {
        if (active) setIsLoading(false);
      }
    }
    void loadAndStart();
    return () => {
      active = false;
    };
  }, [projectId]);

  const sendReply = async (event: FormEvent) => {
    event.preventDefault();
    const userMessage = replyText.trim();
    if (!userMessage) {
      setError("请先输入回复内容。");
      return;
    }
    setIsSending(true);
    setError("");
    setStatus("");
    const currentForm = assistForm;
    const currentMessages = messages;
    try {
      const result = await assistProjectStoryOutline(projectId, {
        action: "reply",
        current_outline: storyFormToPayload(currentForm),
        messages: currentMessages,
        user_message: userMessage
      });
      setMessages([...currentMessages, { role: "user", content: userMessage }, { role: "assistant", content: result.assistant_message }]);
      setReplyText("");
      setFieldNotes(result.field_notes ?? {});
      setLastChangedFields(changedPatchFields(currentForm, result.outline_patch));
      setAssistForm((current) => mergePatchIntoForm(current, result.outline_patch));
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI 协助失败");
    } finally {
      setIsSending(false);
    }
  };

  const confirmSave = async () => {
    if (!completion.is_complete) {
      setError("请先完成故事核心层和结构规划层的必填字段。");
      return;
    }
    setIsSaving(true);
    setError("");
    setStatus("");
    try {
      await updateProjectStoryOutline(projectId, storyFormToPayload(assistForm));
      router.push(`/projects/${projectId}/story-text`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "故事大纲保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="stack assist-page">
      <header className="page-header">
        <div>
          <h1 className="page-title">AI 协助创作故事大纲</h1>
          <p className="page-description">
            {isLoading ? "正在加载项目与 AI 引导..." : `${project?.title ?? "项目"} · 通过对话补齐故事核心层和结构规划层。`}
          </p>
        </div>
        <Link className="button secondary" href={`/projects/${projectId}/story-text`}>
          返回故事大纲
        </Link>
      </header>

      {error ? <div className="error">{error}</div> : null}
      {status ? <div className="success">{status}</div> : null}

      <div className="story-outline-assist-layout">
        <aside className="assist-outline-panel panel stack">
          <div className="section-heading">
            <h2>字段草稿</h2>
            <span className={`status-badge ${completion.is_complete ? "status-active" : "status-review"}`}>
              {completion.completed_fields.length}/{completion.required_fields.length} 必填
            </span>
          </div>
          <div className="assist-completion">
            {completion.is_complete ? "必填字段已完成，可以确认保存。" : `待补充：${completion.missing_fields.map(fieldLabel).join("、")}`}
          </div>

          <div className="outline-field-groups">
            {storyOutlineFieldGroups.map((group) => (
              <section className="outline-field-group assist-outline-group" key={group.id}>
                <div className="outline-field-group-heading">
                  <h3>{group.title}</h3>
                  <p>{group.description}</p>
                </div>
                {group.fields.map((field) => (
                  <AssistTextArea
                    key={field.key}
                    field={field}
                    isRequired={requiredAssistFieldKeys.includes(field.key)}
                    isChanged={lastChangedFields.includes(field.key)}
                    value={assistForm[field.key]}
                    onChange={(value) => setAssistFormValue(field.key, value, setAssistForm, setLastChangedFields)}
                  />
                ))}
                {group.id === "execution" ? (
                  <div className="outline-field-status">
                    <StatusSelect value={assistForm.status} onChange={(value) => setAssistForm((current) => ({ ...current, status: value }))} />
                  </div>
                ) : null}
              </section>
            ))}
          </div>
        </aside>

        <section className="assist-chat-panel panel">
          <div className="assist-chat-header">
            <div>
              <h2>对话引导</h2>
              <p>AI 会根据你的回答更新左侧草稿；确认前不会写入正式故事大纲。</p>
            </div>
            <button className="button" type="button" disabled={!completion.is_complete || isSaving} onClick={() => void confirmSave()}>
              {isSaving ? "保存中..." : "确认保存"}
            </button>
          </div>

          <div className="assist-chat-messages" aria-live="polite">
            {messages.length === 0 ? (
              <div className="assist-empty-message">{isLoading ? "AI 正在准备第一个问题..." : "暂无对话。"}</div>
            ) : (
              messages.map((message, index) => (
                <div className={`assist-message ${message.role}`} key={`${message.role}-${index}`}>
                  <span>{message.role === "assistant" ? "AI" : "我"}</span>
                  <p>{message.content}</p>
                </div>
              ))
            )}
          </div>

          {Object.keys(fieldNotes).length > 0 ? (
            <div className="assist-field-notes">
              <strong>本轮字段更新</strong>
              {Object.entries(fieldNotes).map(([field, note]) => (
                <p key={field}>
                  <span>{fieldLabel(field)}</span>：{note}
                </p>
              ))}
            </div>
          ) : null}

          <form className="assist-input-row" onSubmit={sendReply}>
            <textarea
              value={replyText}
              placeholder="回复 AI 的问题，或直接描述你想要的故事方向。"
              onChange={(event) => setReplyText(event.target.value)}
              rows={4}
            />
            <button className="button" type="submit" disabled={isLoading || isSending}>
              {isSending ? "发送中..." : "发送"}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}

function AssistTextArea({
  field,
  value,
  isRequired,
  isChanged,
  onChange
}: {
  field: StoryOutlineField;
  value: string;
  isRequired: boolean;
  isChanged: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <div className={`field assist-field ${isChanged ? "changed" : ""}`}>
      <label>
        {field.label}
        <span className={`assist-field-tag ${isRequired ? "required" : "optional"}`}>{isRequired ? "必填" : "建议"}</span>
      </label>
      <textarea value={value} placeholder={`${field.description}\n${field.example}`} onChange={(event) => onChange(event.target.value)} rows={3} />
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

function toOptional(value: string) {
  const stripped = value.trim();
  return stripped || undefined;
}

function mergePatchIntoForm(form: StoryOutlineForm, patch: StoryOutlineAssistPatch): StoryOutlineForm {
  const next = { ...form };
  storyOutlineTextFieldKeys.forEach((field) => {
    const value = patch[field];
    if (typeof value === "string" && value.trim()) {
      next[field] = value;
    }
  });
  return next;
}

function changedPatchFields(form: StoryOutlineForm, patch: StoryOutlineAssistPatch): StoryOutlineTextFieldKey[] {
  return storyOutlineTextFieldKeys.filter((field) => {
    const value = patch[field];
    return typeof value === "string" && value.trim() && form[field] !== value;
  });
}

function setAssistFormValue(
  field: StoryOutlineTextFieldKey,
  value: string,
  setAssistForm: Dispatch<SetStateAction<StoryOutlineForm>>,
  setLastChangedFields: Dispatch<SetStateAction<StoryOutlineTextFieldKey[]>>
) {
  setAssistForm((current) => ({ ...current, [field]: value }));
  setLastChangedFields((current) => current.filter((item) => item !== field));
}

function computeCompletion(form: StoryOutlineForm): StoryOutlineAssistCompletion {
  const completed_fields = requiredAssistFieldKeys.filter((field) => form[field].trim());
  const missing_fields = requiredAssistFieldKeys.filter((field) => !completed_fields.includes(field));
  return {
    required_fields: requiredAssistFieldKeys,
    completed_fields,
    missing_fields,
    is_complete: missing_fields.length === 0
  };
}

function fieldLabel(field: string) {
  return fieldLabels[field] ?? field;
}
