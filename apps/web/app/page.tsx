"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { listProjects, ProjectSummary } from "@/lib/api";

export default function ProjectManagementPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    void refreshProjects();
  }, []);

  const refreshProjects = async () => {
    setIsLoading(true);
    setError("");
    try {
      const projectList = await listProjects();
      setProjects(projectList);
    } catch (err) {
      setError(err instanceof Error ? err.message : "项目列表加载失败");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">项目管理</h1>
          <p className="page-description">查看已有短剧项目，继续编辑项目资料，或创建新的短剧项目。</p>
        </div>
        <Button size="lg" asChild>
          <Link href="/projects/new">创建项目</Link>
        </Button>
      </header>

      <section className="panel stack">
        <div className="section-heading">
          <h2>项目列表</h2>
          <span className="hint">{isLoading ? "加载中..." : `${projects.length} 个项目`}</span>
        </div>

        {error ? (
          <div className="stack">
            <div className="error">{error}</div>
            <div className="actions actions-start">
              <Button variant="secondary" type="button" onClick={() => void refreshProjects()}>
                重试
              </Button>
            </div>
          </div>
        ) : null}

        {!isLoading && !error && projects.length === 0 ? (
          <div className="empty-state stack">
            <p>还没有短剧项目。</p>
            <div className="actions actions-start">
              <Button asChild>
                <Link href="/projects/new">创建第一个项目</Link>
              </Button>
            </div>
          </div>
        ) : null}

        {isLoading ? <ListSkeleton /> : null}

        {projects.length > 0 ? (
          <div className="asset-list asset-list-wide">
            {projects.map((project) => (
              <article className="asset-card project-card" key={project.id}>
                <div className="asset-card-main">
                  <div className="asset-card-title">
                    <strong>{project.title}</strong>
                    <Badge className={`status-badge status-${project.status === "draft" ? "draft" : "active"}`}>
                      {project.status === "draft" ? "草稿" : project.status}
                    </Badge>
                  </div>
                  <div className="hint">
                    {project.genre || "未设置题材"} · {project.target_platform || "未设置平台"} · {project.episode_count} 集 ·
                    单集 {formatNumber(project.episode_duration)} 分钟 · 总时长 {formatNumber(project.total_duration)} 分钟
                  </div>
                  <p>{project.idea}</p>
                  <p className="hint">更新时间：{new Date(project.updated_at).toLocaleString()}</p>
                </div>
                <div className="asset-card-actions project-card-actions">
                  <Button variant="secondary" size="lg" asChild>
                    <Link href={`/projects/${project.id}`}>进入工作台</Link>
                  </Button>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </section>
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className="asset-list asset-list-wide" aria-label="项目列表加载中">
      {Array.from({ length: 3 }, (_, index) => (
        <div className="asset-card project-card" key={index}>
          <div className="asset-card-main">
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-4 w-80 max-w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
          <Skeleton className="h-10 w-24" />
        </div>
      ))}
    </div>
  );
}

function formatNumber(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}
