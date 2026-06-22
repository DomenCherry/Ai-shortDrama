"use client";

import { Button } from "@/components/ui/button";
import type { ProjectWorkbenchState } from "../_hooks/useProjectWorkbench";
import {
  setCopyFormValue,
  setShotFormValue
} from "../_utils/workbenchForms";
import { ArtifactStatusBadge, EpisodePicker, NumberInput, ProductionContextSummary, SectionTitle, StatusSelect, TextArea, TextInput } from "./shared";
import { StructuredScriptPanel } from "./StructuredScriptPanel";

export function ProductionModule({ workbench }: { workbench: ProjectWorkbenchState }) {
  if (!workbench.project || workbench.isLandingMode) return null;

  return (
    <>
      {workbench.activeStage === "script" ? <StructuredScriptPanel workbench={workbench} /> : null}
      {workbench.activeStage === "storyboard" ? <StoryboardAndCopywritingPanel workbench={workbench} /> : null}
    </>
  );
}

function StoryboardAndCopywritingPanel({ workbench }: { workbench: ProjectWorkbenchState }) {
  const project = workbench.project;
  if (!project) return null;

  return (
    <section className="panel stack">
      <SectionTitle title="分镜与文案" status={workbench.copywriting?.status ?? workbench.copyForm.status} />
      <EpisodePicker episodeCount={project.episode_count} value={workbench.selectedEpisodeNo} onChange={workbench.setSelectedEpisodeNo} />
      <ProductionContextSummary
        worldSnapshots={workbench.worldSnapshots}
        characterSnapshots={workbench.characterSnapshots}
        storyOutlineStatus={workbench.storyOutlineStatus}
        episodeOutline={workbench.selectedEpisodeOutline}
        episodeContentStatus={workbench.episodeContentStatus}
        projectId={workbench.projectId}
      />
      {workbench.isLoadingEpisodeArtifacts ? <div className="empty-state">正在加载分镜和文案...</div> : null}

      <div className="grid-2">
        <div className="stack">
          <div className="section-heading">
            <h3>镜头列表</h3>
            <Button variant="secondary" type="button" onClick={() => workbench.resetShotForm()}>
              新增镜头
            </Button>
          </div>
          {workbench.storyboardShots.length === 0 ? (
            <div className="empty-state">当前集还没有分镜镜头。</div>
          ) : (
            <div className="asset-list">
              {workbench.storyboardShots.map((shot) => (
                <article className="asset-card" key={shot.id}>
                  <div className="asset-card-title">
                    <strong>镜头 {shot.shot_no}</strong>
                    <ArtifactStatusBadge status={shot.status} />
                  </div>
                  <p>{shot.scene || "未填写场景"}</p>
                  <p className="hint">{shot.visual_prompt || "未填写画面提示词"}</p>
                  <div className="asset-card-actions">
                    <Button variant="secondary" type="button" onClick={() => workbench.editShot(shot)}>
                      编辑
                    </Button>
                    <Button variant="destructive" type="button" onClick={() => void workbench.removeShot(shot)} disabled={workbench.removingShotId === shot.id}>
                      {workbench.removingShotId === shot.id ? "删除中..." : "删除"}
                    </Button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>

        <form className="stack" onSubmit={workbench.saveShot}>
          <h3>{workbench.editingShotId ? "编辑镜头" : "新增镜头"}</h3>
          <div className="grid-2">
            <NumberInput label="镜头序号" min="1" step="1" value={workbench.shotForm.shot_no} onChange={(value) => setShotFormValue("shot_no", value, workbench.setShotForm)} />
            <NumberInput label="镜头时长（秒）" min="0.1" step="0.1" value={workbench.shotForm.duration_seconds} onChange={(value) => setShotFormValue("duration_seconds", value, workbench.setShotForm)} />
          </div>
          <TextArea label="场景/画面" value={workbench.shotForm.scene} onChange={(value) => setShotFormValue("scene", value, workbench.setShotForm)} />
          <TextArea label="画面提示词" value={workbench.shotForm.visual_prompt} onChange={(value) => setShotFormValue("visual_prompt", value, workbench.setShotForm)} />
          <TextArea label="镜头/机位" value={workbench.shotForm.camera} onChange={(value) => setShotFormValue("camera", value, workbench.setShotForm)} />
          <TextArea label="对白或旁白" value={workbench.shotForm.dialogue_or_voiceover} onChange={(value) => setShotFormValue("dialogue_or_voiceover", value, workbench.setShotForm)} />
          <StatusSelect value={workbench.shotForm.status} onChange={(value) => setShotFormValue("status", value, workbench.setShotForm)} />
          <div className="actions">
            <Button variant="secondary" type="button" onClick={() => workbench.resetShotForm()}>
              清空
            </Button>
            <Button type="submit" disabled={workbench.isSaving || !Number.isFinite(Number(workbench.shotForm.shot_no))}>
              {workbench.isSaving ? "保存中..." : "保存镜头"}
            </Button>
          </div>
        </form>
      </div>

      <form className="stack form-section" onSubmit={workbench.saveCopywriting}>
        <h3>字幕与发布文案</h3>
        <div className="grid-2">
          <TextArea label="字幕/剧情内文案" value={workbench.copyForm.subtitles} onChange={(value) => setCopyFormValue("subtitles", value, workbench.setCopyForm)} />
          <TextInput label="平台标题" value={workbench.copyForm.platform_title} onChange={(value) => setCopyFormValue("platform_title", value, workbench.setCopyForm)} />
          <TextArea label="平台简介" value={workbench.copyForm.platform_description} onChange={(value) => setCopyFormValue("platform_description", value, workbench.setCopyForm)} />
          <TextArea label="传播点 / 发布文案" value={workbench.copyForm.publish_copy} onChange={(value) => setCopyFormValue("publish_copy", value, workbench.setCopyForm)} />
        </div>
        <StatusSelect value={workbench.copyForm.status} onChange={(value) => setCopyFormValue("status", value, workbench.setCopyForm)} />
        <div className="actions">
          <Button type="submit" disabled={workbench.isSaving}>
            {workbench.isSaving ? "保存中..." : "保存文案"}
          </Button>
        </div>
      </form>
    </section>
  );
}
