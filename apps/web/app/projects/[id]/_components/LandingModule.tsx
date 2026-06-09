"use client";

import type { ProjectWorkbenchState } from "../_hooks/useProjectWorkbench";
import { artifactStatusLabel, formatNumber } from "../_utils/workbenchForms";
import { Metric, WorkspaceEntryCard } from "./shared";

export function LandingModule({ workbench }: { workbench: ProjectWorkbenchState }) {
  const project = workbench.project;
  if (!project || !workbench.isLandingMode) return null;

  return (
    <>
      <section className="panel stack">
        <div className="section-heading">
          <h2>项目概览</h2>
          <span className={`status-badge status-${project.status === "draft" ? "draft" : "active"}`}>
            {project.status === "draft" ? "草稿" : project.status}
          </span>
        </div>
        <div className="metric-grid">
          <Metric label="题材" value={project.genre || "未设置"} />
          <Metric label="平台" value={project.target_platform || "未设置"} />
          <Metric label="集数" value={`${project.episode_count} 集`} />
          <Metric label="单集时长" value={`${formatNumber(project.episode_duration)} 分钟`} />
          <Metric label="总时长" value={`${formatNumber(project.total_duration)} 分钟`} />
        </div>
        <p>{project.idea}</p>
        <p className="hint">更新时间：{new Date(project.updated_at).toLocaleString()}</p>
      </section>

      <section className="workspace-entry-grid" aria-label="项目工作台入口">
        <WorkspaceEntryCard
          title="项目资料 / 资产"
          description="基础信息、世界观和角色是后续内容的公共上下文。"
          href={`/projects/${workbench.projectId}/assets`}
          isActive={!workbench.isLandingMode && workbench.activeWorkspaceGroup.key === "projectAssets"}
          metrics={[
            workbench.worldSnapshots.length > 0 ? `世界观：${workbench.worldSnapshots[0].name}` : "世界观：未加载",
            `角色：${workbench.characterSnapshots.length} 个`,
            project.idea ? "基础信息：已填写" : "基础信息：待补充"
          ]}
        />
        <WorkspaceEntryCard
          title="故事文本"
          description="形成可读的故事 / 小说化文本，短剧制作必须以单集故事正文为输入。"
          href={`/projects/${workbench.projectId}/story-text`}
          isActive={!workbench.isLandingMode && workbench.activeWorkspaceGroup.key === "storyText"}
          metrics={[
            `整体大纲：${artifactStatusLabel(workbench.storyOutlineStatus)}`,
            `分集大纲：${workbench.filledEpisodeOutlineCount}/${project.episode_count}`,
            `当前集正文：${artifactStatusLabel(workbench.episodeContentStatus)}`
          ]}
        />
        <WorkspaceEntryCard
          title="短剧制作"
          description="沿用已选世界观、角色和单集故事正文，生成视频生产需要的文字内容。"
          href={`/projects/${workbench.projectId}/production`}
          isActive={!workbench.isLandingMode && workbench.activeWorkspaceGroup.key === "production"}
          metrics={[
            `第 ${workbench.selectedEpisodeNo} 集剧本：${artifactStatusLabel(workbench.episodeScriptStatus)}`,
            `分镜：${workbench.storyboardShots.length} 个镜头`,
            `文案：${artifactStatusLabel(workbench.copywritingStatus)}`
          ]}
        />
      </section>
    </>
  );
}
