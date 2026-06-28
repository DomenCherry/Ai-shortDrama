"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import {
  listModelConfigs,
  deleteModelConfig,
  enableModelConfig,
} from "@/lib/api";
import type { ModelConfig } from "@/lib/api";

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
  const [videoConfigs, setVideoConfigs] = useState<ModelConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");
  const [configPendingDelete, setConfigPendingDelete] = useState<ModelConfig | null>(null);

  const loadAll = async () => {
    setLoading(true);
    setError("");
    try {
      const [text, image, video] = await Promise.all([
        listModelConfigs("text"),
        listModelConfigs("image"),
        listModelConfigs("video"),
      ]);
      setTextConfigs(text);
      setImageConfigs(image);
      setVideoConfigs(video);
    } catch (err) {
      setError(err instanceof Error ? err.message : "模型配置列表加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleDelete = (config: ModelConfig) => {
    setConfigPendingDelete(config);
  };

  const confirmDelete = async () => {
    if (!configPendingDelete) return;
    setError("");
    setStatusMessage("");
    try {
      await deleteModelConfig(configPendingDelete.id);
      setStatusMessage("配置已删除。");
      setConfigPendingDelete(null);
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
      <ConfirmDialog
        destructive
        open={Boolean(configPendingDelete)}
        title="删除模型配置？"
        description={
          configPendingDelete
            ? `确定删除「${configPendingDelete.provider_name} - ${configPendingDelete.model_name}」吗？删除后该配置将从列表移除，历史测试记录会保留。`
            : ""
        }
        confirmLabel="删除"
        onOpenChange={(open) => {
          if (!open) setConfigPendingDelete(null);
        }}
        onConfirm={() => void confirmDelete()}
      />
      <header className="page-header">
        <div>
          <h1 className="page-title">模型 API 配置</h1>
          <p className="page-description">
            配置文本生成、图片生成和文生视频模型。保存后点击测试连接，测试成功后才能执行对应生成任务。
          </p>
        </div>
      </header>

      {statusMessage ? <div className="success">{statusMessage}</div> : null}
      {error ? <div className="error">{error}</div> : null}

      <div className="model-config-grid">
        <ConfigList
          title="文本生成模型"
          configs={textConfigs}
          loading={loading}
          onEnable={handleEnable}
          onDelete={handleDelete}
          onEdit={(config) => router.push(`/settings/edit?id=${config.id}&type=${config.config_type}`)}
          onNew={() => router.push("/settings/edit?type=text")}
        />
        <ConfigList
          title="图片生成模型"
          configs={imageConfigs}
          loading={loading}
          onEnable={handleEnable}
          onDelete={handleDelete}
          onEdit={(config) => router.push(`/settings/edit?id=${config.id}&type=${config.config_type}`)}
          onNew={() => router.push("/settings/edit?type=image")}
        />
        <ConfigList
          title="文生视频模型"
          configs={videoConfigs}
          loading={loading}
          onEnable={handleEnable}
          onDelete={handleDelete}
          onEdit={(config) => router.push(`/settings/edit?id=${config.id}&type=${config.config_type}`)}
          onNew={() => router.push("/settings/edit?type=video")}
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
  configs: ModelConfig[];
  loading: boolean;
  onEnable: (config: ModelConfig) => void;
  onDelete: (config: ModelConfig) => void;
  onEdit: (config: ModelConfig) => void;
  onNew: () => void;
}) {
  return (
    <div className="panel stack">
      <div className="section-heading">
        <h2>{title}</h2>
        <Button onClick={onNew}>
          新建配置
        </Button>
      </div>

      {loading ? (
        <ConfigSkeleton />
      ) : configs.length > 0 ? (
        <div className="stack stack-compact">
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
                  <Badge className={`status-badge status-test-${config.last_test_status || "untested"}`}>
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
                    variant="secondary"
                    size="sm"
                    onClick={() => onEnable(config)}
                  >
                    设为启用
                  </Button>
                ) : null}
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => onEdit(config)}
                >
                  编辑
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
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

function ConfigSkeleton() {
  return (
    <div className="stack stack-compact" aria-label="配置列表加载中">
      {Array.from({ length: 2 }, (_, index) => (
        <div className="asset-card" key={index}>
          <div className="asset-card-main">
            <Skeleton className="h-5 w-44" />
            <Skeleton className="h-4 w-56 max-w-full" />
          </div>
          <div className="asset-card-actions">
            <Skeleton className="h-9 w-20" />
            <Skeleton className="h-9 w-14" />
          </div>
        </div>
      ))}
    </div>
  );
}
