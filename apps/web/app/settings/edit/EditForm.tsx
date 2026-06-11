"use client";

import { FormEvent, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { SimpleSelect } from "@/components/ui/simple-select";
import {
  getModelConfig,
  createModelConfig,
  updateModelConfig,
  testModelConfig,
} from "@/lib/api";
import type { ModelConfigPayload, ModelConfigUpdatePayload } from "@/lib/api";

type ConfigType = "text" | "image";
type ProviderMode = "custom" | "preset";

type FormState = {
  provider_mode: ProviderMode;
  provider_preset: string;
  provider_name: string;
  api_base_url: string;
  api_key: string;
  model_name: string;
  image_size: string;
  endpoint_path: string;
  supports_reference_image: boolean;
  remark: string;
};

const emptyForm: FormState = {
  provider_mode: "custom",
  provider_preset: "",
  provider_name: "",
  api_base_url: "",
  api_key: "",
  model_name: "",
  image_size: "1024x1024",
  endpoint_path: "/images/generations",
  supports_reference_image: false,
  remark: "",
};

const imageProviderPresets = {
  volcengine_seedream: {
    label: "火山方舟 Seedream",
    provider_name: "火山方舟 Seedream",
    api_base_url: "https://ark.cn-beijing.volces.com/api/v3",
    endpoint_path: "/images/generations",
    supports_reference_image: true,
    image_size: "1024x1024",
  },
};

export default function SettingsEditPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const configType = (searchParams.get("type") as ConfigType) || "text";
  const editingId = searchParams.get("id");

  const [form, setForm] = useState<FormState>(emptyForm);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testConfigId, setTestConfigId] = useState<string | null>(null);

  useEffect(() => {
    if (editingId) {
      setLoading(true);
      getModelConfig(editingId)
        .then((config) => {
          setForm({
            provider_mode: config.provider_mode,
            provider_preset: config.provider_preset || "",
            provider_name: config.provider_name,
            api_base_url: config.api_base_url,
            api_key: "",
            model_name: config.model_name,
            image_size: config.image_size || "1024x1024",
            endpoint_path: config.endpoint_path || "/images/generations",
            supports_reference_image: config.supports_reference_image,
            remark: config.remark || "",
          });
          setTestConfigId(config.id);
        })
        .catch(() => setError("加载配置失败"))
        .finally(() => setLoading(false));
    }
  }, [editingId]);

  const updateField = (field: keyof FormState, value: string | boolean) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const updateProviderMode = (value: ProviderMode) => {
    if (value === "custom") {
      setForm((current) => ({
        ...current,
        provider_mode: "custom",
        provider_preset: "",
        supports_reference_image: false,
      }));
      return;
    }
    applyImagePreset("volcengine_seedream");
  };

  const applyImagePreset = (presetKey: keyof typeof imageProviderPresets) => {
    const preset = imageProviderPresets[presetKey];
    setForm((current) => ({
      ...current,
      provider_mode: "preset",
      provider_preset: presetKey,
      provider_name: preset.provider_name,
      api_base_url: preset.api_base_url,
      endpoint_path: preset.endpoint_path,
      supports_reference_image: preset.supports_reference_image,
      image_size: current.image_size || preset.image_size,
    }));
  };

  const saveConfig = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setStatus("");
    setIsSaving(true);

    try {
      if (editingId) {
        const payload: ModelConfigUpdatePayload = {
          provider_mode: configType === "image" ? form.provider_mode : "custom",
          provider_preset:
            configType === "image" && form.provider_mode === "preset"
              ? form.provider_preset
              : undefined,
          provider_name: form.provider_name,
          api_base_url: form.api_base_url,
          model_name: form.model_name,
          image_size: configType === "image" ? form.image_size : undefined,
          endpoint_path: configType === "image" ? form.endpoint_path : undefined,
          supports_reference_image: configType === "image" ? form.supports_reference_image : undefined,
          remark: form.remark,
        };
        if (form.api_key.trim()) {
          payload.api_key = form.api_key.trim();
        }
        await updateModelConfig(editingId, payload);
        setStatus("配置已更新，请重新测试连接。");
      } else {
        const payload: ModelConfigPayload = {
          config_type: configType,
          provider_mode: configType === "image" ? form.provider_mode : "custom",
          provider_preset:
            configType === "image" && form.provider_mode === "preset"
              ? form.provider_preset
              : undefined,
          provider_name: form.provider_name,
          api_base_url: form.api_base_url,
          api_key: form.api_key,
          model_name: form.model_name,
          image_size: configType === "image" ? form.image_size : undefined,
          endpoint_path: configType === "image" ? form.endpoint_path : undefined,
          supports_reference_image: configType === "image" ? form.supports_reference_image : undefined,
          remark: form.remark,
          enabled: true,
        };
        const created = await createModelConfig(payload);
        setTestConfigId(created.id);
        setStatus("配置已保存，请测试连接。");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "配置保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const testConnection = async () => {
    const targetId = testConfigId || editingId;
    if (!targetId) {
      setError("请先保存配置");
      return;
    }

    setError("");
    setStatus("");
    setIsTesting(true);

    try {
      const response = (await testModelConfig(targetId)) as {
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

  const goBack = () => router.push("/settings");

  if (loading) {
    return (
      <div className="main">
        <div className="panel stack">
          <p className="hint">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="main">
      <div className="stack form-page">
        <header className="page-header">
          <div>
            <h1 className="page-title">{editingId ? "编辑配置" : "新建配置"}</h1>
            <p className="page-description">
              {configType === "text" ? "文本生成模型" : "图片生成模型"}
            </p>
          </div>
        </header>

        <div className="panel stack">
          <form className="stack" onSubmit={saveConfig}>
            {configType === "image" ? (
              <div className="field">
                <label>配置方式</label>
                <SimpleSelect
                  value={form.provider_mode}
                  onValueChange={(value) => updateProviderMode(value as ProviderMode)}
                  options={[
                    { label: "自定义供应商", value: "custom" },
                    { label: "供应商预设", value: "preset" }
                  ]}
                />
                <span className="hint">预设用于快速填充常见供应商参数，自定义配置可接入其他图片模型。</span>
              </div>
            ) : null}
            {configType === "image" && form.provider_mode === "preset" ? (
              <div className="field">
                <label>供应商预设</label>
                <SimpleSelect
                  value={form.provider_preset}
                  onValueChange={(value) => applyImagePreset(value as keyof typeof imageProviderPresets)}
                  options={Object.entries(imageProviderPresets).map(([key, preset]) => ({ label: preset.label, value: key }))}
                />
                <span className="hint">
                  火山方舟 Seedream 支持角色三视图和参考图输入，模型名称仍需填写你实际开通的模型。
                </span>
              </div>
            ) : null}
            <div className="field">
              <label>供应商名称</label>
              <Input
                value={form.provider_name}
                onChange={(event) => updateField("provider_name", event.target.value)}
                readOnly={configType === "image" && form.provider_mode === "preset"}
                placeholder="例如 OpenAI-compatible"
              />
            </div>
            <div className="field">
              <label>API Base URL</label>
              <Input
                value={form.api_base_url}
                onChange={(event) => updateField("api_base_url", event.target.value)}
                readOnly={configType === "image" && form.provider_mode === "preset"}
                placeholder={
                  configType === "text"
                    ? "例如 https://ark.cn-beijing.volces.com/api/v3"
                    : "https://api.example.com/v1"
                }
              />
              {configType === "text" ? (
                <span className="hint">
                  文本模型只填写 Base URL，系统会自动调用 /chat/completions。
                </span>
              ) : null}
            </div>
            <div className="field">
              <label>API Key</label>
              <Input
                type="password"
                value={form.api_key}
                onChange={(event) => updateField("api_key", event.target.value)}
                placeholder={editingId ? "已保存，留空则保持不变" : "输入密钥"}
              />
              <span className="hint">密钥不会出现在 Markdown 导出中。</span>
            </div>
            <div className="field">
              <label>模型名称</label>
              <Input
                value={form.model_name}
                onChange={(event) => updateField("model_name", event.target.value)}
                placeholder={configType === "text" ? "text-model" : "image-model"}
              />
            </div>
            {configType === "image" ? (
              <>
                <div className="field">
                  <label>图片尺寸</label>
                  <SimpleSelect
                    value={form.image_size}
                    onValueChange={(value) => updateField("image_size", value)}
                    options={[
                      { label: "1024x1024", value: "1024x1024" },
                      { label: "1024x1536", value: "1024x1536" },
                      { label: "1536x1024", value: "1536x1024" },
                      { label: "2K", value: "2K" },
                      { label: "4K", value: "4K" }
                    ]}
                  />
                </div>
                <div className="field">
                  <label>图片接口路径</label>
                  <Input
                    value={form.endpoint_path}
                    onChange={(event) => updateField("endpoint_path", event.target.value)}
                    readOnly={form.provider_mode === "preset"}
                    placeholder="/images/generations"
                  />
                  <span className="hint">系统会将 API Base URL 和接口路径拼接后调用图片生成接口。</span>
                </div>
                <label className="checkbox-field">
                  <Checkbox
                    checked={form.supports_reference_image}
                    disabled={form.provider_mode === "preset"}
                    onCheckedChange={(checked) => updateField("supports_reference_image", checked === true)}
                  />
                  <span>该图片模型支持参考图输入</span>
                </label>
              </>
            ) : null}
            <div className="field">
              <label>备注</label>
              <Input
                value={form.remark}
                onChange={(event) => updateField("remark", event.target.value)}
              />
            </div>

            {status ? <div className="success">{status}</div> : null}
            {error ? <div className="error">{error}</div> : null}

            <div className="actions">
              <Button
                variant="secondary"
                type="button"
                onClick={testConnection}
                disabled={isTesting}
              >
                {isTesting ? "测试中..." : "测试连接"}
              </Button>
              <Button type="submit" disabled={isSaving}>
                {isSaving ? "保存中..." : editingId ? "更新配置" : "保存配置"}
              </Button>
            </div>
          </form>
        </div>

        <div className="actions" style={{ justifyContent: "flex-start" }}>
          <Button variant="secondary" onClick={goBack}>
            ← 返回配置列表
          </Button>
        </div>
      </div>
    </div>
  );
}
