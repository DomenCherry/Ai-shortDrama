"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  listModelConfigs,
  deleteModelConfig,
  enableModelConfig,
} from "@/lib/api";
import type { ModelConfig } from "@/lib/api";

type ConfigType = "text" | "image";

function formatDateTime(iso?: string) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("zh-CN");
}

function testStatusLabel(status: string) {
  if (status === "success") return "测试成功";
  if (status === "failed") return "测试失败";
  return "未测试";
}

export default function SettingsPage() {
  const router = useRouter();
  const [textConfigs, setTextConfigs] = useState<ModelConfig[]>([]);
  const [imageConfigs, setImageConfigs] = useState<ModelConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");

  const loadAll = async () => {
    setLoading(true);
    setError("");
    try {
      const [text, image] = await Promise.all([
        listModelConfigs("text"),
        listModelConfigs("image"),
      ]);
      setTextConfigs(text);
      setImageConfigs(image);
    } catch (err) {
      setError(err instanceof Error ? err.message : "模型配置列表加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleDelete = async (config: ModelConfig) => {
    if (!confirm(`确定删除「${config.provider_name} - ${config.model_name}」吗？删除后该配置将从列表移除，历史测试记录会保留。`)) {
      return;
    }
    setError("");
    setStatusMessage("");
    try {
      await deleteModelConfig(config.id);
      setStatusMessage("配置已删除。");
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  };

  const handleEnable = async (config: ModelConfig) => {
    setError("");
    setStatusMessage("");
    try {
      await enableModelConfig(config.id);
      setStatusMessage("配置已设为启用。");
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "启用失败");
    }
  };

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

      {statusMessage ? <div className="success">{statusMessage}</div> : null}
      {error ? <div className="error">{error}</div> : null}

      <div className="grid-2">
        <ConfigList
          title="文本生成模型"
          configType="text"
          configs={textConfigs}
          loading={loading}
          onEnable={handleEnable}
          onDelete={handleDelete}
          onEdit={(id) => router.push(`/settings/edit?id=${id}`)}
          onNew={() => router.push("/settings/edit?type=text")}
        />
        <ConfigList
          title="图片生成模型"
          configType="image"
          configs={imageConfigs}
          loading={loading}
          onEnable={handleEnable}
          onDelete={handleDelete}
          onEdit={(id) => router.push(`/settings/edit?id=${id}`)}
          onNew={() => router.push("/settings/edit?type=image")}
        />
      </div>
    </div>
  );
}

function ConfigList({
  title,
  configs,
  loading,
  onEnable,
  onDelete,
  onEdit,
  onNew,
}: {
  title: string;
  configType: ConfigType;
  configs: ModelConfig[];
  loading: boolean;
  onEnable: (config: ModelConfig) => void;
  onDelete: (config: ModelConfig) => void;
  onEdit: (id: string) => void;
  onNew: () => void;
}) {
  return (
    <div className="panel stack">
      <div className="section-heading">
        <h2>{title}</h2>
        <Button className="button" onClick={onNew}>
          新建配置
        </Button>
      </div>

      {loading ? (
        <p className="hint">加载中...</p>
      ) : configs.length > 0 ? (
        <div className="stack" style={{ gap: 8 }}>
          {configs.map((config) => (
            <div key={config.id} className="asset-card">
              <div className="asset-card-main">
                <div className="asset-card-title">
                  <strong>{config.provider_name}</strong>
                  <span className="hint">{config.model_name}</span>
                  {config.enabled ? (
                    <Badge className="status-badge status-active">已启用</Badge>
                  ) : (
                    <Badge className="status-badge status-draft">未启用</Badge>
                  )}
                  <Badge
                    className="status-badge"
                    style={{
                      background:
                        config.last_test_status === "success"
                          ? "#e3f5ef"
                          : config.last_test_status === "failed"
                          ? "#f9e7e4"
                          : "#edf0f2",
                      color:
                        config.last_test_status === "success"
                          ? "var(--brand-strong)"
                          : config.last_test_status === "failed"
                          ? "var(--danger)"
                          : "#3f474d",
                    }}
                  >
                    {testStatusLabel(config.last_test_status)}
                  </Badge>
                </div>
                <div className="meta-line">
                  <span className="hint">
                    更新时间：{formatDateTime(config.updated_at)}
                  </span>
                </div>
              </div>
              <div className="asset-card-actions">
                {!config.enabled ? (
                  <Button
                    className="button secondary"
                    style={{ padding: "6px 10px", fontSize: 13 }}
                    onClick={() => onEnable(config)}
                  >
                    设为启用
                  </Button>
                ) : null}
                <Button
                  className="button secondary"
                  style={{ padding: "6px 10px", fontSize: 13 }}
                  onClick={() => onEdit(config.id)}
                >
                  编辑
                </Button>
                <Button
                  className="button danger"
                  style={{ padding: "6px 10px", fontSize: 13 }}
                  onClick={() => onDelete(config)}
                >
                  删除
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">暂无配置，点击上方按钮新建。</div>
      )}
    </div>
  );
}
