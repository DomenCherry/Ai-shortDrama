"use client";

import { FormEvent, useState } from "react";
import { createModelConfig, testModelConfig } from "@/lib/api";

type ConfigType = "text" | "image";

type FormState = {
  provider_name: string;
  api_base_url: string;
  api_key: string;
  model_name: string;
  image_size: string;
  remark: string;
};

const emptyForm: FormState = {
  provider_name: "",
  api_base_url: "",
  api_key: "",
  model_name: "",
  image_size: "1024x1024",
  remark: ""
};

export default function SettingsPage() {
  return (
    <div className="stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">模型 API 配置</h1>
          <p className="page-description">
            配置文本生成模型和图片生成模型。保存后点击测试连接，测试成功后才能执行对应生成任务。
          </p>
        </div>
      </header>

      <div className="grid-2">
        <ModelConfigForm title="文本生成模型" configType="text" />
        <ModelConfigForm title="图片生成模型" configType="image" />
      </div>
    </div>
  );
}

function ModelConfigForm({ title, configType }: { title: string; configType: ConfigType }) {
  const [form, setForm] = useState<FormState>(emptyForm);
  const [savedConfigId, setSavedConfigId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  const updateField = (field: keyof FormState, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const saveConfig = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setStatus("");
    setIsSaving(true);

    try {
      const response = (await createModelConfig({
        config_type: configType,
        provider_name: form.provider_name,
        api_base_url: form.api_base_url,
        api_key: form.api_key,
        model_name: form.model_name,
        image_size: configType === "image" ? form.image_size : undefined,
        remark: form.remark,
        enabled: true
      })) as { id: string };
      setSavedConfigId(response.id);
      setStatus("配置已保存，请测试连接。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "配置保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const testConnection = async () => {
    if (!savedConfigId) {
      setError("请先保存配置");
      return;
    }

    setError("");
    setStatus("");
    setIsTesting(true);

    try {
      const response = (await testModelConfig(savedConfigId)) as {
        success: boolean;
        message: string;
        tested_at: string;
      };
      if (response.success) {
        setStatus(`测试成功：${response.tested_at}`);
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "接口测试失败");
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <form className="panel stack" onSubmit={saveConfig}>
      <h2>{title}</h2>
      <div className="field">
        <label>供应商名称</label>
        <input
          value={form.provider_name}
          onChange={(event) => updateField("provider_name", event.target.value)}
          placeholder="例如 OpenAI-compatible"
        />
      </div>
      <div className="field">
        <label>API Base URL</label>
        <input
          value={form.api_base_url}
          onChange={(event) => updateField("api_base_url", event.target.value)}
          placeholder="https://api.example.com/v1"
        />
      </div>
      <div className="field">
        <label>API Key</label>
        <input
          type="password"
          value={form.api_key}
          onChange={(event) => updateField("api_key", event.target.value)}
          placeholder="输入密钥"
        />
        <span className="hint">密钥不会出现在 Markdown 导出中。</span>
      </div>
      <div className="field">
        <label>模型名称</label>
        <input
          value={form.model_name}
          onChange={(event) => updateField("model_name", event.target.value)}
          placeholder={configType === "text" ? "text-model" : "image-model"}
        />
      </div>
      {configType === "image" ? (
        <div className="field">
          <label>图片尺寸</label>
          <select value={form.image_size} onChange={(event) => updateField("image_size", event.target.value)}>
            <option value="1024x1024">1024x1024</option>
            <option value="1024x1536">1024x1536</option>
            <option value="1536x1024">1536x1024</option>
          </select>
        </div>
      ) : null}
      <div className="field">
        <label>备注</label>
        <input value={form.remark} onChange={(event) => updateField("remark", event.target.value)} />
      </div>

      {status ? <div className="success">{status}</div> : null}
      {error ? <div className="error">{error}</div> : null}

      <div className="actions">
        <button className="button secondary" type="button" onClick={testConnection} disabled={isTesting}>
          {isTesting ? "测试中..." : "测试连接"}
        </button>
        <button className="button" type="submit" disabled={isSaving}>
          {isSaving ? "保存中..." : "保存配置"}
        </button>
      </div>
    </form>
  );
}

