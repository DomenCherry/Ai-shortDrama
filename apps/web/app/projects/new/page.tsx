"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { createProject } from "@/lib/api";

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

const initialForm: ProjectForm = {
  title: "",
  idea: "",
  target_platform: "抖音",
  genre: "",
  episode_count: "20",
  episode_duration: "1",
  target_audience: "",
  style: "",
  remark: ""
};

export default function NewProjectPage() {
  const router = useRouter();
  const [form, setForm] = useState<ProjectForm>(initialForm);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const episodeCount = Number(form.episode_count);
  const episodeDuration = Number(form.episode_duration);
  const totalDuration = useMemo(() => episodeCount * episodeDuration, [episodeCount, episodeDuration]);
  const validationError = validateProject(form, episodeCount, episodeDuration, totalDuration);

  const updateField = (field: keyof ProjectForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const submitProject = async (event: FormEvent) => {
    event.preventDefault();
    setStatus("");
    setError("");

    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    try {
      const project = await createProject({
        title: form.title || undefined,
        idea: form.idea,
        target_platform: form.target_platform,
        genre: form.genre || undefined,
        episode_count: episodeCount,
        episode_duration: episodeDuration,
        target_audience: form.target_audience || undefined,
        style: form.style || undefined,
        remark: form.remark || undefined
      });
      setStatus("项目创建成功，正在进入项目工作台。");
      setForm(initialForm);
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "项目创建失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">创建短剧项目</h1>
          <p className="page-description">
            先确定创意和项目体量。单集时长不能超过 2 分钟，总时长不能超过 240 分钟。
          </p>
        </div>
        <Link className="button secondary" href="/">
          返回项目管理
        </Link>
      </header>

      <form className="panel stack" onSubmit={submitProject}>
        <div className="field">
          <label>创意描述</label>
          <textarea
            value={form.idea}
            onChange={(event) => updateField("idea", event.target.value)}
            placeholder="例如：都市逆袭爽剧，女主被丈夫背叛后发现自己是豪门继承人。"
          />
        </div>

        <div className="grid-2">
          <div className="field">
            <label>项目名称</label>
            <input
              value={form.title}
              onChange={(event) => updateField("title", event.target.value)}
              placeholder="未填写时保存为未命名短剧"
            />
          </div>
          <div className="field">
            <label>目标平台</label>
            <input value={form.target_platform} onChange={(event) => updateField("target_platform", event.target.value)} />
          </div>
          <div className="field">
            <label>题材类型</label>
            <input
              value={form.genre}
              onChange={(event) => updateField("genre", event.target.value)}
              placeholder="都市逆袭、古装重生、悬疑反转"
            />
          </div>
          <div className="field">
            <label>目标受众</label>
            <input
              value={form.target_audience}
              onChange={(event) => updateField("target_audience", event.target.value)}
              placeholder="例如 18-35 岁女性用户"
            />
          </div>
          <div className="field">
            <label>内容风格</label>
            <input
              value={form.style}
              onChange={(event) => updateField("style", event.target.value)}
              placeholder="爽感强、节奏快、反转密集"
            />
          </div>
          <div className="field">
            <label>备注</label>
            <input value={form.remark} onChange={(event) => updateField("remark", event.target.value)} />
          </div>
        </div>

        <div className="grid-2">
          <div className="field">
            <label>集数</label>
            <input
              type="number"
              min="1"
              step="1"
              value={form.episode_count}
              onChange={(event) => updateField("episode_count", event.target.value)}
            />
          </div>
          <div className="field">
            <label>单集时长（分钟）</label>
            <input
              type="number"
              min="0.1"
              max="2"
              step="0.1"
              value={form.episode_duration}
              onChange={(event) => updateField("episode_duration", event.target.value)}
            />
          </div>
        </div>

        <div className="summary-box">
          <strong>总时长：</strong>
          {Number.isFinite(totalDuration) ? `${formatNumber(totalDuration)} 分钟` : "请填写集数和单集时长"}
          {Number.isFinite(episodeDuration) && episodeDuration > 0 ? (
            <span className="hint">，单集约 {formatNumber(episodeDuration * 60)} 秒</span>
          ) : null}
        </div>

        {validationError ? <div className="error">{validationError}</div> : null}
        {error ? <div className="error">{error}</div> : null}
        {status ? <div className="success">{status}</div> : null}

        <div className="actions">
          <Link className="button secondary" href="/">
            取消
          </Link>
          <button className="button" type="submit" disabled={isSubmitting || Boolean(validationError)}>
            {isSubmitting ? "创建中..." : "创建项目"}
          </button>
        </div>
      </form>
    </div>
  );
}

function validateProject(
  form: ProjectForm,
  episodeCount: number,
  episodeDuration: number,
  totalDuration: number
) {
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

function formatNumber(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}
