"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { ProjectWorkbenchState } from "../_hooks/useProjectWorkbench";
import { episodeAiActions, productionAiActions } from "../_utils/workbenchTypes";

export function LoadingWorkbench() {
  return (
    <div className="stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">项目工作台</h1>
          <p className="page-description">正在加载项目资料...</p>
        </div>
      </header>
      <section className="panel stack" aria-label="项目工作台加载中">
        <Skeleton className="h-5 w-52" />
        <div className="metric-grid">
          {Array.from({ length: 5 }, (_, index) => (
            <Skeleton className="h-16" key={index} />
          ))}
        </div>
        <Skeleton className="h-28 w-full" />
      </section>
    </div>
  );
}

export function MissingProject({ error }: { error: string }) {
  return (
    <div className="stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">项目工作台</h1>
          <p className="page-description">无法读取项目资料。</p>
        </div>
        <Button variant="secondary" asChild>
          <Link href="/">返回项目管理</Link>
        </Button>
      </header>
      {error ? <div className="error">{error}</div> : null}
    </div>
  );
}

export function WorkbenchHeader({ workbench }: { workbench: ProjectWorkbenchState }) {
  const project = workbench.project;
  if (!project) return null;

  const showEpisodeAiActions = workbench.currentWorkspaceGroup?.key === "storyText" && workbench.activeStage === "content";
  const showProductionAiActions = workbench.currentWorkspaceGroup?.key === "production";
  const moduleFunctionActions = showEpisodeAiActions ? episodeAiActions : showProductionAiActions ? productionAiActions : [];

  if (workbench.isLandingMode) {
    return (
      <header className="page-header">
        <div>
          <h1 className="page-title">{project.title}</h1>
          <p className="page-description">
            先维护项目资料和资产，再完成故事文本，最后把单集故事正文转换为短剧制作文本。上游变更后，下游内容会提示需要检查。
          </p>
        </div>
        <div className="actions">
          <Button variant="secondary" asChild>
            <Link href="/">返回项目管理</Link>
          </Button>
        </div>
      </header>
    );
  }

  return (
    <header className="module-toolbar">
      <div className="module-toolbar-title">
        <h1>{workbench.currentWorkspaceGroup?.title}</h1>
        <span title={workbench.currentWorkspaceGroup?.description}>当前项目：{project.title}</span>
      </div>
      <div className={`module-toolbar-center ${moduleFunctionActions.length > 0 ? "has-functions" : ""}`}>
        <nav
          className="module-subnav module-stage-switcher"
          aria-label={`${workbench.currentWorkspaceGroup?.title ?? "模块"}内容导航`}
        >
          {workbench.visibleStages.map((stage) => (
            <Button
              aria-current={workbench.activeStage === stage.key ? "page" : undefined}
              className={`module-subnav-tab ${workbench.activeStage === stage.key ? "active" : ""}`}
              type="button"
              variant="ghost"
              key={stage.key}
              onClick={() => {
                if (workbench.activeStage === "storyboard" && stage.key !== "storyboard") {
                  window.dispatchEvent(new CustomEvent("storyboard-stage-switch", { detail: stage.key }));
                  return;
                }
                workbench.setActiveStage(stage.key);
              }}
            >
              <span>{stage.label}</span>
              {workbench.currentWorkspaceGroup?.key === "projectAssets" && stage.key === "world" ? (
                <span className="module-stage-count">{workbench.worldSnapshots.length}/1</span>
              ) : null}
              {workbench.currentWorkspaceGroup?.key === "projectAssets" && stage.key === "characters" ? (
                <span className="module-stage-count">{workbench.characterSnapshots.length}</span>
              ) : null}
            </Button>
          ))}
        </nav>
        {moduleFunctionActions.length > 0 ? (
          <div className="module-function-strip" aria-label="AI 功能入口">
            {moduleFunctionActions.map((action) => (
              <Button
                className="module-ai-action"
                type="button"
                variant="ghost"
                key={action}
                disabled={
                  action === "正文创作" &&
                  (!workbench.canGenerateEpisodeContent || workbench.isGeneratingContent)
                }
                title={
                  action === "正文创作" && !workbench.canGenerateEpisodeContent
                    ? "请先完善并保存本集分集大纲"
                    : undefined
                }
                onClick={() =>
                  action === "正文创作"
                    ? workbench.openEpisodeContentCreator()
                    : workbench.showAiPlaceholder(action)
                }
              >
                {action}
              </Button>
            ))}
          </div>
        ) : null}
      </div>
      <div className="module-toolbar-actions">
        <Button className="compact-action" variant="secondary" asChild>
          <Link href={`/projects/${workbench.projectId}`}>工作台入口</Link>
        </Button>
      </div>
    </header>
  );
}

export function WorkbenchStatusStrip({ workbench }: { workbench: ProjectWorkbenchState }) {
  if (!workbench.error && !workbench.status && !workbench.assetError && !workbench.artifactError) return null;

  return (
    <div className="module-status-strip">
      {workbench.error ? <span className="error">{workbench.error}</span> : null}
      {workbench.status ? <span className="success">{workbench.status}</span> : null}
      {workbench.assetError ? <span className="error">{workbench.assetError}</span> : null}
      {workbench.artifactError ? <span className="error">{workbench.artifactError}</span> : null}
    </div>
  );
}
