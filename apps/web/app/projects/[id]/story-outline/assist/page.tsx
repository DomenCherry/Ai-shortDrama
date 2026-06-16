"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import { useParams, useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SimpleSelect } from "@/components/ui/simple-select";
import { Textarea } from "@/components/ui/textarea";
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
  StoryOutlineAssistResult,
  updateProjectStoryOutline
} from "@/lib/api";
import { storyOutlineFieldGroups, StoryOutlineField, StoryOutlineTextFieldKey } from "../../storyOutlineFields";

type StoryOutlineForm = Record<StoryOutlineTextFieldKey, string> & {
  status: ProjectArtifactStatus;
};

type AssistProcessStage = "idle" | "loading_context" | "calling_model" | "parsing" | "updating";

type AssistRunMeta = {
  requestId: string;
  elapsedMs: number;
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
  const [processStage, setProcessStage] = useState<AssistProcessStage>("loading_context");
  const [processingStartedAt, setProcessingStartedAt] = useState<number | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [activeRequestId, setActiveRequestId] = useState("");
  const [lastRunMeta, setLastRunMeta] = useState<AssistRunMeta | null>(null);

  const completion = useMemo(() => computeCompletion(assistForm), [assistForm]);
  const hasSavableContent = useMemo(() => hasAnyStoryOutlineContent(assistForm), [assistForm]);
  const isProcessing = isLoading || isSending;

  useEffect(() => {
    if (!processingStartedAt) return undefined;
    const timer = window.setInterval(() => {
      const nextElapsedSeconds = Math.floor((Date.now() - processingStartedAt) / 1000);
      setElapsedSeconds(nextElapsedSeconds);
      if (processStage === "loading_context" && nextElapsedSeconds >= 2) {
        setProcessStage("calling_model");
      }
    }, 1000);
    return () => window.clearInterval(timer);
  }, [processStage, processingStartedAt]);

  useEffect(() => {
    let active = true;
    async function loadAndStart() {
      setIsLoading(true);
      setError("");
      setStatus("");
      const requestId = createClientRequestId();
      startProcessing(requestId, "loading_context", setActiveRequestId, setProcessingStartedAt, setElapsedSeconds, setProcessStage, setLastRunMeta);
      try {
        const [projectResult, outline] = await Promise.all([getProject(projectId), getProjectStoryOutline(projectId)]);
        if (!active) return;
        const initialForm = storyPayloadToForm(outline ?? emptyStoryForm);
        setProject(projectResult);
        setAssistForm(initialForm);
        setProcessStage("calling_model");
        const result = await assistProjectStoryOutline(projectId, {
          action: "start",
          current_outline: storyFormToPayload(initialForm),
          messages: [],
          user_message: undefined,
          client_request_id: requestId
        });
        if (!active) return;
        setProcessStage("parsing");
        setMessages([{ role: "assistant", content: result.assistant_message }]);
        setFieldNotes(result.field_notes ?? {});
        const changedFields = changedPatchFields(initialForm, result.outline_patch);
        setLastChangedFields(changedFields);
        setProcessStage("updating");
        setAssistForm((current) => mergePatchIntoForm(current, result.outline_patch));
        setLastRunMeta(toRunMeta(result, requestId));
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "AI 协助初始化失败");
      } finally {
        if (active) {
          setIsLoading(false);
          stopProcessing(setProcessingStartedAt, setProcessStage, setActiveRequestId);
        }
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
    const requestId = createClientRequestId();
    startProcessing(requestId, "loading_context", setActiveRequestId, setProcessingStartedAt, setElapsedSeconds, setProcessStage, setLastRunMeta);
    setMessages([...currentMessages, { role: "user", content: userMessage }]);
    try {
      setProcessStage("calling_model");
      const result = await assistProjectStoryOutline(projectId, {
        action: "reply",
        current_outline: storyFormToPayload(currentForm),
        messages: currentMessages,
        user_message: userMessage,
        client_request_id: requestId
      });
      setProcessStage("parsing");
      setMessages([...currentMessages, { role: "user", content: userMessage }, { role: "assistant", content: result.assistant_message }]);
      setReplyText("");
      setFieldNotes(result.field_notes ?? {});
      setLastChangedFields(changedPatchFields(currentForm, result.outline_patch));
      setProcessStage("updating");
      setAssistForm((current) => mergePatchIntoForm(current, result.outline_patch));
      setLastRunMeta(toRunMeta(result, requestId));
    } catch (err) {
      setMessages(currentMessages);
      setError(err instanceof Error ? err.message : "AI 协助失败");
    } finally {
      setIsSending(false);
      stopProcessing(setProcessingStartedAt, setProcessStage, setActiveRequestId);
    }
  };

  const confirmSave = async () => {
    if (!hasSavableContent) {
      setError("请先填写或通过 AI 生成至少一个故事大纲字段后再保存。");
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
        <Button variant="secondary" asChild>
          <Link href={`/projects/${projectId}/story-text`}>返回故事大纲</Link>
        </Button>
      </header>

      {error ? <div className="error">{error}</div> : null}
      {status ? <div className="success">{status}</div> : null}

      <div className="story-outline-assist-layout">
        <aside className="assist-outline-panel panel stack">
          <div className="section-heading">
            <h2>字段草稿</h2>
            <Badge className={`status-badge ${completion.is_complete ? "status-active" : "status-review"}`}>
              {completion.completed_fields.length}/{completion.required_fields.length} 必填
            </Badge>
          </div>
          <div className="assist-completion">
            {completion.is_complete
              ? "必填字段已完成，可以保存或继续打磨。"
              : `可先保存当前内容；待补充：${completion.missing_fields.map(fieldLabel).join("、")}`}
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
              <p>AI 会根据你的回答更新左侧草稿；你可以阶段性保存，不必等全部必填字段完成。</p>
            </div>
            <Button type="button" disabled={!hasSavableContent || isSaving} onClick={() => void confirmSave()}>
              {isSaving ? "保存中..." : "保存当前内容"}
            </Button>
          </div>

          <div className="assist-chat-messages" aria-live="polite">
            {messages.length === 0 && !isProcessing ? <div className="assist-empty-message">暂无对话。</div> : null}
            {messages.map((message, index) => (
              <div className={`assist-message ${message.role}`} key={`${message.role}-${index}`}>
                <span>{message.role === "assistant" ? "AI" : "我"}</span>
                <p>{message.content}</p>
              </div>
            ))}
            {isProcessing ? (
              <div className="assist-message assistant pending">
                <span>AI</span>
                <p>{isLoading ? "正在准备第一个问题..." : "已收到，正在整理项目上下文..."}</p>
              </div>
            ) : null}
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

          <AssistProcessingStatus
            isProcessing={isProcessing}
            stage={processStage}
            elapsedSeconds={elapsedSeconds}
            requestId={activeRequestId}
            lastRunMeta={lastRunMeta}
          />

          <form className="assist-input-row" onSubmit={sendReply}>
            <Textarea
              value={replyText}
              placeholder="回复 AI 的问题，或直接描述你想要的故事方向。"
              onChange={(event) => setReplyText(event.target.value)}
              rows={4}
            />
            <Button type="submit" disabled={isLoading || isSending}>
              {isSending ? "发送中..." : "发送"}
            </Button>
          </form>
        </section>
      </div>
    </div>
  );
}

function AssistProcessingStatus({
  isProcessing,
  stage,
  elapsedSeconds,
  requestId,
  lastRunMeta
}: {
  isProcessing: boolean;
  stage: AssistProcessStage;
  elapsedSeconds: number;
  requestId: string;
  lastRunMeta: AssistRunMeta | null;
}) {
  if (!isProcessing && !lastRunMeta) return null;
  if (!isProcessing && lastRunMeta) {
    return (
      <div className="assist-process-status complete">
        <span>本轮完成</span>
        <p>
          用时 {formatElapsedMs(lastRunMeta.elapsedMs)} / 请求编号 {lastRunMeta.requestId}
        </p>
      </div>
    );
  }
  return (
    <div className="assist-process-status">
      <span>{assistStageLabel(stage)}</span>
      <p>
        已等待 {elapsedSeconds} 秒
        {requestId ? ` / 请求编号 ${requestId}` : ""}
      </p>
      <small>{assistWaitingHint(elapsedSeconds)}</small>
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
      <Textarea value={value} placeholder={`${field.description}\n${field.example}`} onChange={(event) => onChange(event.target.value)} rows={3} />
    </div>
  );
}

function StatusSelect({ value, onChange }: { value: ProjectArtifactStatus; onChange: (value: ProjectArtifactStatus) => void }) {
  return (
    <div className="field compact-field">
      <label>状态</label>
      <SimpleSelect
        value={value}
        onValueChange={(nextValue) => onChange(nextValue as ProjectArtifactStatus)}
        options={[
          { label: "草稿", value: "draft" },
          { label: "已确认", value: "confirmed" },
          { label: "需要检查", value: "needs_review" }
        ]}
      />
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

function hasAnyStoryOutlineContent(form: StoryOutlineForm) {
  return storyOutlineTextFieldKeys.some((field) => form[field].trim());
}

function fieldLabel(field: string) {
  return fieldLabels[field] ?? field;
}

function createClientRequestId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `assist-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
}

function startProcessing(
  requestId: string,
  stage: AssistProcessStage,
  setActiveRequestId: Dispatch<SetStateAction<string>>,
  setProcessingStartedAt: Dispatch<SetStateAction<number | null>>,
  setElapsedSeconds: Dispatch<SetStateAction<number>>,
  setProcessStage: Dispatch<SetStateAction<AssistProcessStage>>,
  setLastRunMeta: Dispatch<SetStateAction<AssistRunMeta | null>>
) {
  setActiveRequestId(requestId);
  setProcessingStartedAt(Date.now());
  setElapsedSeconds(0);
  setProcessStage(stage);
  setLastRunMeta(null);
}

function stopProcessing(
  setProcessingStartedAt: Dispatch<SetStateAction<number | null>>,
  setProcessStage: Dispatch<SetStateAction<AssistProcessStage>>,
  setActiveRequestId: Dispatch<SetStateAction<string>>
) {
  setProcessingStartedAt(null);
  setProcessStage("idle");
  setActiveRequestId("");
}

function toRunMeta(result: StoryOutlineAssistResult, fallbackRequestId: string): AssistRunMeta {
  return {
    requestId: result.request_id || fallbackRequestId,
    elapsedMs: typeof result.elapsed_ms === "number" ? result.elapsed_ms : 0
  };
}

function assistStageLabel(stage: AssistProcessStage) {
  const labels: Record<AssistProcessStage, string> = {
    idle: "等待输入",
    loading_context: "整理项目上下文",
    calling_model: "调用文本模型",
    parsing: "解析字段建议",
    updating: "更新左侧草稿"
  };
  return labels[stage];
}

function assistWaitingHint(elapsedSeconds: number) {
  if (elapsedSeconds >= 60) {
    return "已等待较久，可继续等待，或稍后重试 / 检查模型配置。";
  }
  if (elapsedSeconds >= 30) {
    return "模型仍在处理，通常与模型响应速度有关，可以继续等待。";
  }
  return "请求已发送，正在等待 AI 返回结构化字段建议。";
}

function formatElapsedMs(elapsedMs: number) {
  if (elapsedMs <= 0) return "不足 1 秒";
  if (elapsedMs < 1000) return `${elapsedMs} 毫秒`;
  return `${(elapsedMs / 1000).toFixed(1)} 秒`;
}
