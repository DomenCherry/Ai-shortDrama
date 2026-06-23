"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { listUserSkills, updateUserSkill } from "@/lib/api";
import type { UserSkill } from "@/lib/api";

function formatDateTime(iso?: string) {
  if (!iso) return "默认启用，尚未修改";
  return new Date(iso).toLocaleString("zh-CN");
}

export default function SkillsPage() {
  const [skills, setSkills] = useState<UserSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [pendingSkill, setPendingSkill] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");

  const loadSkills = async () => {
    setLoading(true);
    setError("");
    try {
      setSkills(await listUserSkills());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Skill 列表加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadSkills();
  }, []);

  const toggleSkill = async (skill: UserSkill) => {
    setPendingSkill(skill.name);
    setStatusMessage("");
    setError("");
    try {
      const updated = await updateUserSkill(skill.name, { enabled: !skill.enabled });
      setSkills((currentSkills) => currentSkills.map((item) => (item.name === updated.name ? updated : item)));
      setStatusMessage(`${updated.name} 已${updated.enabled ? "启用" : "禁用"}。`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Skill 状态更新失败");
    } finally {
      setPendingSkill("");
    }
  };

  return (
    <div className="stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Skill 管理</h1>
          <p className="page-description">
            管理项目内用户侧业务 Skill。禁用后，依赖该 Skill 的 AI 生成能力会停止调用，但不会影响已保存内容和手动编辑。
          </p>
        </div>
      </header>

      {statusMessage ? <div className="success">{statusMessage}</div> : null}
      {error ? <div className="error">{error}</div> : null}

      <section className="panel stack">
        <div className="section-heading">
          <h2>用户侧业务 Skill</h2>
          <span className="hint">{loading ? "加载中..." : `${skills.length} 个 Skill`}</span>
        </div>

        {loading ? <SkillListSkeleton /> : null}

        {!loading && skills.length === 0 ? (
          <div className="empty-state">
            <p>当前没有可管理的用户侧业务 Skill。</p>
          </div>
        ) : null}

        {!loading && skills.length > 0 ? (
          <div className="asset-list asset-list-wide">
            {skills.map((skill) => {
              const isPending = pendingSkill === skill.name;
              return (
                <article className="asset-card project-card" key={skill.name}>
                  <div className="asset-card-main">
                    <div className="asset-card-title">
                      <strong>{skill.name}</strong>
                      {skill.enabled ? (
                        <Badge className="status-badge status-active">已启用</Badge>
                      ) : (
                        <Badge className="status-badge status-draft">已禁用</Badge>
                      )}
                    </div>
                    <p>{skill.description || "未填写 Skill 描述。"}</p>
                    <div className="meta-line">
                      <span className="hint">来源：{skill.source_dir}</span>
                      <span className="hint">更新时间：{formatDateTime(skill.updated_at)}</span>
                    </div>
                  </div>
                  <div className="asset-card-actions project-card-actions">
                    <Button
                      disabled={isPending}
                      size="sm"
                      type="button"
                      variant={skill.enabled ? "destructive" : "secondary"}
                      onClick={() => void toggleSkill(skill)}
                    >
                      {isPending ? "处理中..." : skill.enabled ? "禁用" : "启用"}
                    </Button>
                  </div>
                </article>
              );
            })}
          </div>
        ) : null}
      </section>
    </div>
  );
}

function SkillListSkeleton() {
  return (
    <div className="asset-list asset-list-wide" aria-label="Skill 列表加载中">
      {Array.from({ length: 2 }, (_, index) => (
        <div className="asset-card project-card" key={index}>
          <div className="asset-card-main">
            <Skeleton className="h-5 w-52" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-72 max-w-full" />
          </div>
          <Skeleton className="h-9 w-16" />
        </div>
      ))}
    </div>
  );
}
