"use client";

import { FormEvent, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { SimpleSelect } from "@/components/ui/simple-select";
import {
  getModelConfig,
  createModelConfig,
  updateModelConfig,
  testModelConfig,
} from "@/lib/api";
import type { ModelConfigPayload, ModelConfigType, ModelConfigUpdatePayload } from "@/lib/api";

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

const videoProviderPresets = {
  volcengine_seedance_1_5: {
    label: "火山方舟",
    provider_name: "火山方舟",
    api_base_url: "https://ark.cn-beijing.volces.com/api/v3",
    endpoint_path: "/contents/generations/tasks",
    model_name: "",
  },
};

export default function SettingsEditPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const requestedConfigType = parseConfigType(searchParams.get("type"));
  const editingId = searchParams.get("id");

  const [form, setForm] = useState<FormState>(emptyForm);
  const [loadedConfigType, setLoadedConfigType] = useState<ModelConfigType | null>(null);
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
          setLoadedConfigType(config.config_type);
          setForm({
            provider_mode: config.provider_mode,
            provider_preset: config.provider_preset || "",
            provider_name: config.provider_name,
            api_base_url: config.api_base_url,
            api_key: "",
            model_name: config.model_name,
            image_size: config.image_size || defaultSizeForConfigType(config.config_type),
            endpoint_path: config.endpoint_path || defaultEndpointForConfigType(config.config_type),
            supports_reference_image: config.supports_reference_image,
            remark: config.remark || "",
          });
          setTestConfigId(config.id);
        })
        .catch(() => setError("加载配置失败"))
        .finally(() => setLoading(false));
      return;
    }
    setLoadedConfigType(null);
    setTestConfigId(null);
    setForm(defaultFormForConfigType(requestedConfigType));
  }, [editingId, requestedConfigType]);

  const configType = loadedConfigType || requestedConfigType;
  const isImageConfig = configType === "image";
  const isVideoConfig = configType === "video";
  const supportsProviderPresets = isImageConfig || isVideoConfig;
  const isVideoPresetConfig = isVideoConfig && form.provider_mode === "preset";
  const usesEndpointConfig = isImageConfig || isVideoConfig;
  const configTypeLabel = getConfigTypeLabel(configType);

  const updateField = (field: keyof FormState, value: string | boolean) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const updateProviderMode = (value: ProviderMode) => {
    if (value === "custom") {
      setForm((current) => ({
        ...current,
        provider_mode: "custom",
        provider_preset: "",
        provider_name: "",
        api_base_url: "",
        model_name: "",
        endpoint_path: defaultEndpointForConfigType(configType),
        image_size: defaultSizeForConfigType(configType),
        supports_reference_image: false,
      }));
      return;
    }
    if (isImageConfig) {
      applyImagePreset("volcengine_seedream");
    } else if (isVideoConfig) {
      applyVideoPreset("volcengine_seedance_1_5");
    }
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

  const applyVideoPreset = (presetKey: keyof typeof videoProviderPresets) => {
    const preset = videoProviderPresets[presetKey];
    setForm((current) => ({
      ...current,
      provider_mode: "preset",
      provider_preset: presetKey,
      provider_name: preset.provider_name,
      api_base_url: preset.api_base_url,
      endpoint_path: preset.endpoint_path,
      model_name: current.model_name || preset.model_name,
      image_size: "",
      supports_reference_image: false,
    }));
  };

  const saveConfig = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setStatus("");
    setIsSaving(true);

    try {
      const modelName = form.model_name.trim();
      if (!modelName) {
        setError(
          isVideoPresetConfig
            ? "请填写火山方舟控制台中已开通的 Seedance Model ID 或推理接入点 Endpoint ID。"
            : "请填写模型名称。"
        );
        return;
      }

      if (editingId) {
        const payload: ModelConfigUpdatePayload = {
          provider_mode: supportsProviderPresets ? form.provider_mode : "custom",
          provider_preset:
            supportsProviderPresets && form.provider_mode === "preset"
              ? form.provider_preset
              : undefined,
          provider_name: form.provider_name,
          api_base_url: form.api_base_url,
          model_name: modelName,
          image_size: isImageConfig ? form.image_size : undefined,
          endpoint_path: usesEndpointConfig ? form.endpoint_path : undefined,
          supports_reference_image: isImageConfig ? form.supports_reference_image : undefined,
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
          provider_mode: supportsProviderPresets ? form.provider_mode : "custom",
          provider_preset:
            supportsProviderPresets && form.provider_mode === "preset"
              ? form.provider_preset
              : undefined,
          provider_name: form.provider_name,
          api_base_url: form.api_base_url,
          api_key: form.api_key.trim(),
          model_name: modelName,
          image_size: isImageConfig ? form.image_size : undefined,
          endpoint_path: usesEndpointConfig ? form.endpoint_path : undefined,
          supports_reference_image: isImageConfig ? form.supports_reference_image : undefined,
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
              {configTypeLabel}
            </p>
          </div>
        </header>

        <div className="panel stack">
          <form className="stack" onSubmit={saveConfig}>
            {supportsProviderPresets ? (
              <Field label="配置方式" hint="预设用于快速填充常见供应商参数，自定义配置可接入其他模型。">
                <SimpleSelect
                  value={form.provider_mode}
                  onValueChange={(value) => updateProviderMode(value as ProviderMode)}
                  options={[
                    { label: "自定义供应商", value: "custom" },
                    { label: "供应商预设", value: "preset" }
                  ]}
                />
              </Field>
            ) : null}
            {supportsProviderPresets && form.provider_mode === "preset" ? (
              <Field
                label="供应商预设"
                hint={isVideoConfig ? "Seedance 1.5 Pro 使用火山方舟视频生成任务接口，需填写控制台中已开通的 Model ID 或 Endpoint ID。" : "火山方舟 Seedream 支持角色三视图和参考图输入，模型名称仍需填写你实际开通的模型。"}
              >
                <SimpleSelect
                  value={form.provider_preset}
                  onValueChange={(value) => {
                    if (isVideoConfig) {
                      applyVideoPreset(value as keyof typeof videoProviderPresets);
                    } else {
                      applyImagePreset(value as keyof typeof imageProviderPresets);
                    }
                  }}
                  options={Object.entries(isVideoConfig ? videoProviderPresets : imageProviderPresets).map(([key, preset]) => ({ label: preset.label, value: key }))}
                />
              </Field>
            ) : null}
            <Field label="供应商名称">
              <Input
                value={form.provider_name}
                onChange={(event) => updateField("provider_name", event.target.value)}
                readOnly={supportsProviderPresets && form.provider_mode === "preset"}
                placeholder={isVideoConfig ? "例如 OpenAI-compatible 视频供应商" : "例如 OpenAI-compatible"}
              />
            </Field>
            <Field
              label="API Base URL"
              hint={getApiBaseUrlHint(configType)}
            >
              <Input
                value={form.api_base_url}
                onChange={(event) => updateField("api_base_url", event.target.value)}
                readOnly={supportsProviderPresets && form.provider_mode === "preset"}
                placeholder={configType === "text" ? "例如 https://ark.cn-beijing.volces.com/api/v3" : "https://api.example.com/v1"}
              />
            </Field>
            <Field label="API Key" hint="密钥不会出现在 Markdown 导出中。">
              <Input
                type="password"
                value={form.api_key}
                onChange={(event) => updateField("api_key", event.target.value)}
                placeholder={editingId ? "已保存，留空则保持不变" : "输入密钥"}
              />
            </Field>
            <Field
              label={isVideoPresetConfig ? "Model ID / Endpoint ID" : "模型名称"}
              hint={getModelNameHint(configType, isVideoPresetConfig)}
            >
              <Input
                value={form.model_name}
                onChange={(event) => updateField("model_name", event.target.value)}
                placeholder={getModelNamePlaceholder(configType)}
              />
            </Field>
            {usesEndpointConfig ? (
              <>
                {isImageConfig ? (
                  <Field label="图片尺寸">
                    <SimpleSelect
                      value={form.image_size}
                      onValueChange={(value) => updateField("image_size", value)}
                      options={getSizeOptions(configType)}
                    />
                  </Field>
                ) : null}
                <Field
                  label={isVideoConfig ? "视频接口路径" : "图片接口路径"}
                  hint={`系统会将 API Base URL 和接口路径拼接后调用${isVideoConfig ? "文生视频" : "图片生成"}接口。`}
                >
                  <Input
                    value={form.endpoint_path}
                    onChange={(event) => updateField("endpoint_path", event.target.value)}
                    readOnly={form.provider_mode === "preset"}
                    placeholder={defaultEndpointForConfigType(configType)}
                  />
                </Field>
                {isVideoPresetConfig ? (
                  <div className="warning-text">
                    测试连接会向火山方舟创建一个最小视频生成任务并返回任务 ID，可能产生模型调用费用。真实生成参数将在项目或分镜调用时设置。
                  </div>
                ) : null}
                {isImageConfig ? (
                  <label className="checkbox-field">
                    <Checkbox
                      checked={form.supports_reference_image}
                      disabled={form.provider_mode === "preset"}
                      onCheckedChange={(checked) => updateField("supports_reference_image", checked === true)}
                    />
                    <span>该图片模型支持参考图输入</span>
                  </label>
                ) : null}
              </>
            ) : null}
            <Field label="备注">
              <Input
                value={form.remark}
                onChange={(event) => updateField("remark", event.target.value)}
              />
            </Field>

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

        <div className="actions actions-start">
          <Button variant="secondary" onClick={goBack}>
            ← 返回配置列表
          </Button>
        </div>
      </div>
    </div>
  );
}

function parseConfigType(value: string | null): ModelConfigType {
  if (value === "image" || value === "video") return value;
  return "text";
}

function defaultFormForConfigType(configType: ModelConfigType): FormState {
  if (configType === "video") {
    const preset = videoProviderPresets.volcengine_seedance_1_5;
    return {
      ...emptyForm,
      provider_mode: "preset",
      provider_preset: "volcengine_seedance_1_5",
      provider_name: preset.provider_name,
      api_base_url: preset.api_base_url,
      model_name: preset.model_name,
      image_size: "",
      endpoint_path: preset.endpoint_path,
      supports_reference_image: false,
    };
  }

  return {
    ...emptyForm,
    image_size: defaultSizeForConfigType(configType),
    endpoint_path: defaultEndpointForConfigType(configType),
  };
}

function defaultEndpointForConfigType(configType: ModelConfigType) {
  if (configType === "image") return "/images/generations";
  if (configType === "video") return "/videos/generations";
  return "";
}

function defaultSizeForConfigType(configType: ModelConfigType) {
  if (configType === "video") return "1280x720";
  return "1024x1024";
}

function getConfigTypeLabel(configType: ModelConfigType) {
  if (configType === "image") return "图片生成模型";
  if (configType === "video") return "文生视频模型";
  return "文本生成模型";
}

function getApiBaseUrlHint(configType: ModelConfigType) {
  if (configType === "text") return "文本模型只填写 Base URL，系统会自动调用 /chat/completions。";
  if (configType === "video") return "Seedance 预设使用火山方舟 API Base URL，自定义视频供应商可手动填写。";
  return undefined;
}

function getModelNamePlaceholder(configType: ModelConfigType) {
  if (configType === "image") return "image-model";
  if (configType === "video") return "从火山方舟控制台复制 Endpoint ID 或已开通 Model ID";
  return "text-model";
}

function getModelNameHint(configType: ModelConfigType, isVideoPresetConfig: boolean) {
  if (isVideoPresetConfig) return "不要直接使用示例名；测试连接会按这里填写的 ID 创建 Seedance 视频任务。";
  if (configType === "video") return "自定义视频供应商按其 API 要求填写模型名。";
  return undefined;
}

function getSizeOptions(configType: ModelConfigType) {
  if (configType === "video") {
    return [
      { label: "1280x720", value: "1280x720" },
      { label: "720x1280", value: "720x1280" },
      { label: "1920x1080", value: "1920x1080" },
      { label: "1080x1920", value: "1080x1920" },
      { label: "1024x1024", value: "1024x1024" },
    ];
  }
  return [
    { label: "1024x1024", value: "1024x1024" },
    { label: "1024x1536", value: "1024x1536" },
    { label: "1536x1024", value: "1536x1024" },
    { label: "2K", value: "2K" },
    { label: "4K", value: "4K" },
  ];
}
