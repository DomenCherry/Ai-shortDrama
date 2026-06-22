"use client";

import { Button } from "@/components/ui/button";
import type { ProjectWorkbenchState } from "../_hooks/useProjectWorkbench";
import { setCopyFormValue } from "../_utils/workbenchForms";
import { EpisodePicker, SectionTitle, StatusSelect, TextArea, TextInput } from "./shared";
import { StructuredScriptPanel } from "./StructuredScriptPanel";
import { StoryboardWorkbench } from "./StoryboardWorkbench";

export function ProductionModule({ workbench }: { workbench: ProjectWorkbenchState }) {
  if (!workbench.project || workbench.isLandingMode) return null;

  return (
    <>
      {workbench.activeStage === "script" ? <StructuredScriptPanel workbench={workbench} /> : null}
      {workbench.activeStage === "storyboard" ? <StoryboardWorkbench workbench={workbench} /> : null}
      {workbench.activeStage === "copywriting" ? <CopywritingPanel workbench={workbench} /> : null}
    </>
  );
}

function CopywritingPanel({ workbench }: { workbench: ProjectWorkbenchState }) {
  const project = workbench.project;
  if (!project) return null;

  return (
    <section className="panel stack">
      <SectionTitle title="字幕与发布文案" status={workbench.copywriting?.status ?? workbench.copyForm.status} />
      <EpisodePicker episodeCount={project.episode_count} value={workbench.selectedEpisodeNo} onChange={workbench.setSelectedEpisodeNo} />
      <form className="stack" onSubmit={workbench.saveCopywriting}>
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
