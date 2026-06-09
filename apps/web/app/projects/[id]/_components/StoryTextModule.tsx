"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { SimpleSelect } from "@/components/ui/simple-select";
import type { ProjectArtifactStatus } from "@/lib/api";
import type { ProjectWorkbenchState } from "../_hooks/useProjectWorkbench";
import {
  setContentFormValue,
  setEpisodeFormValue,
  setStoryFormValue,
  worldSnapshotSummary
} from "../_utils/workbenchForms";
import { referenceTabs } from "../_utils/workbenchTypes";
import { storyOutlineFieldGroups } from "../storyOutlineFields";
import { ArtifactStatusBadge, EpisodePicker, NumberInput, ReferenceCard, SectionTitle, StatusSelect, TextArea, TextInput } from "./shared";

export function StoryTextModule({ workbench }: { workbench: ProjectWorkbenchState }) {
  if (!workbench.project || workbench.isLandingMode) return null;

  return (
    <>
      {workbench.activeStage === "story" ? <StoryOutlinePanel workbench={workbench} /> : null}
      {workbench.activeStage === "episodes" ? <EpisodeOutlinePanel workbench={workbench} /> : null}
      {workbench.activeStage === "content" ? <EpisodeContentPanel workbench={workbench} /> : null}
    </>
  );
}

function StoryOutlinePanel({ workbench }: { workbench: ProjectWorkbenchState }) {
  return (
    <section className="panel stack">
      <div className="story-outline-header">
        <h2>整体故事大纲</h2>
        <div className="story-outline-header-meta">
          <ArtifactStatusBadge status={workbench.storyOutline?.status ?? workbench.storyForm.status} />
        </div>
        <div className="story-outline-header-actions">
          <Button className="button secondary compact-button" asChild>
            <Link href={`/projects/${workbench.projectId}/story-outline/assist`}>AI协助</Link>
          </Button>
          <Button className="button secondary compact-button" asChild>
            <Link href={`/projects/${workbench.projectId}/story-outline/extract`}>AI提取</Link>
          </Button>
        </div>
      </div>
      <form className="stack" onSubmit={workbench.saveStoryOutline}>
        <div className="outline-field-groups">
          {storyOutlineFieldGroups.map((group) => (
            <section className="outline-field-group" key={group.id}>
              <div className="outline-field-group-heading">
                <h3>{group.title}</h3>
                <p>{group.description}</p>
              </div>
              <div className="grid-2">
                {group.fields.map((field) => (
                  <TextArea
                    key={field.key}
                    label={field.label}
                    placeholder={`${field.description}\n${field.example}`}
                    value={workbench.storyForm[field.key]}
                    onChange={(value) => setStoryFormValue(field.key, value, workbench.setStoryForm)}
                  />
                ))}
              </div>
              {group.id === "execution" ? (
                <div className="outline-field-status">
                  <StatusSelect value={workbench.storyForm.status} onChange={(value) => setStoryFormValue("status", value, workbench.setStoryForm)} />
                </div>
              ) : null}
            </section>
          ))}
        </div>
        <div className="actions">
          <Button className="button" type="submit" disabled={workbench.isSaving}>
            {workbench.isSaving ? "保存中..." : "保存整体大纲"}
          </Button>
        </div>
      </form>
    </section>
  );
}

function EpisodeOutlinePanel({ workbench }: { workbench: ProjectWorkbenchState }) {
  const project = workbench.project;
  if (!project) return null;

  return (
    <section className="panel stack">
      <SectionTitle title="分集大纲" status={workbench.episodeOutlines.find((outline) => outline.episode_no === workbench.selectedEpisodeNo)?.status ?? workbench.episodeForm.status} />
      <div className="episode-workspace">
        <aside className="episode-index" aria-label="分集列表">
          <EpisodePicker episodeCount={project.episode_count} value={workbench.selectedEpisodeNo} onChange={workbench.setSelectedEpisodeNo} />
          <div className="episode-index-list">
            {workbench.episodeRows.map((row) => (
              <Button
                className={`episode-index-item ${workbench.selectedEpisodeNo === row.episodeNo ? "active" : ""}`}
                type="button"
                variant="ghost"
                key={row.episodeNo}
                onClick={() => workbench.setSelectedEpisodeNo(row.episodeNo)}
                aria-current={workbench.selectedEpisodeNo === row.episodeNo ? "true" : undefined}
              >
                <span className="episode-index-main">
                  <strong>第 {row.episodeNo} 集</strong>
                  <span className="episode-index-meta">
                    <ArtifactStatusBadge status={row.outline?.status ?? "draft"} />
                  </span>
                </span>
                <span className="episode-index-title">{row.outline?.title || "未填写标题"}</span>
              </Button>
            ))}
          </div>
        </aside>

        <form className="episode-editor stack" onSubmit={workbench.saveEpisodeOutline}>
          <div className="episode-editor-heading">
            <h3>编辑第 {workbench.selectedEpisodeNo} 集</h3>
            <ArtifactStatusBadge status={workbench.episodeOutlines.find((outline) => outline.episode_no === workbench.selectedEpisodeNo)?.status ?? workbench.episodeForm.status} />
          </div>
          <div className="grid-2">
            <TextInput label="标题" value={workbench.episodeForm.title} onChange={(value) => setEpisodeFormValue("title", value, workbench.setEpisodeForm)} />
            <NumberInput label="预计时长（分钟）" min="0.1" step="0.1" value={workbench.episodeForm.duration_minutes} onChange={(value) => setEpisodeFormValue("duration_minutes", value, workbench.setEpisodeForm)} />
            <TextArea label="本集梗概" value={workbench.episodeForm.synopsis} onChange={(value) => setEpisodeFormValue("synopsis", value, workbench.setEpisodeForm)} />
            <TextArea label="开场钩子" value={workbench.episodeForm.hook} onChange={(value) => setEpisodeFormValue("hook", value, workbench.setEpisodeForm)} />
            <TextArea label="本集冲突" value={workbench.episodeForm.conflict} onChange={(value) => setEpisodeFormValue("conflict", value, workbench.setEpisodeForm)} />
            <TextArea label="反转" value={workbench.episodeForm.reversal} onChange={(value) => setEpisodeFormValue("reversal", value, workbench.setEpisodeForm)} />
            <TextArea label="结尾悬念" value={workbench.episodeForm.cliffhanger} onChange={(value) => setEpisodeFormValue("cliffhanger", value, workbench.setEpisodeForm)} />
          </div>
          <StatusSelect value={workbench.episodeForm.status} onChange={(value) => setEpisodeFormValue("status", value, workbench.setEpisodeForm)} />
          <div className="actions">
            <Button className="button" type="submit" disabled={workbench.isSaving}>
              {workbench.isSaving ? "保存中..." : "保存分集大纲"}
            </Button>
          </div>
        </form>
      </div>
    </section>
  );
}

function EpisodeContentPanel({ workbench }: { workbench: ProjectWorkbenchState }) {
  const project = workbench.project;
  if (!project) return null;

  return (
    <section className="panel stack">
      <form className="episode-writing-form stack" onSubmit={workbench.saveEpisodeContent}>
        {workbench.isLoadingEpisodeArtifacts ? <div className="empty-state">正在加载单集故事正文...</div> : null}

        <div className="episode-writing-workspace">
          <aside className="episode-index writing-episode-index" aria-label="单集故事正文分集列表">
            <EpisodePicker episodeCount={project.episode_count} value={workbench.selectedEpisodeNo} onChange={workbench.setSelectedEpisodeNo} />
            <div className="episode-index-list">
              {workbench.episodeRows.map((row) => (
                <Button
                  className={`episode-index-item ${workbench.selectedEpisodeNo === row.episodeNo ? "active" : ""}`}
                  type="button"
                  variant="ghost"
                  key={row.episodeNo}
                  onClick={() => workbench.setSelectedEpisodeNo(row.episodeNo)}
                  aria-current={workbench.selectedEpisodeNo === row.episodeNo ? "true" : undefined}
                >
                  <span className="episode-index-main">
                    <strong>第 {row.episodeNo} 集</strong>
                    <span className="episode-index-meta">
                      {workbench.selectedEpisodeNo === row.episodeNo ? (
                        <ArtifactStatusBadge status={workbench.episodeContent?.status ?? workbench.contentForm.status} />
                      ) : (
                        <ArtifactStatusBadge status={row.outline?.status ?? "draft"} />
                      )}
                    </span>
                  </span>
                  <span className="episode-index-title">{row.outline?.title || "未填写标题"}</span>
                </Button>
              ))}
            </div>
          </aside>

          <aside className="writing-context-panel" aria-label="大纲参考与正文元信息">
            <ReferenceCard title="上游大纲参考">
              <dl className="outline-reference-list">
                <div>
                  <dt>标题</dt>
                  <dd>{workbench.selectedEpisodeOutline?.title || "未填写标题"}</dd>
                </div>
                <div>
                  <dt>本集梗概</dt>
                  <dd>{workbench.selectedEpisodeOutline?.synopsis || "未填写"}</dd>
                </div>
                <div>
                  <dt>开场钩子</dt>
                  <dd>{workbench.selectedEpisodeOutline?.hook || "未填写"}</dd>
                </div>
                <div>
                  <dt>本集冲突</dt>
                  <dd>{workbench.selectedEpisodeOutline?.conflict || "未填写"}</dd>
                </div>
                <div>
                  <dt>关键反转</dt>
                  <dd>{workbench.selectedEpisodeOutline?.reversal || "未填写"}</dd>
                </div>
                <div>
                  <dt>结尾悬念</dt>
                  <dd>{workbench.selectedEpisodeOutline?.cliffhanger || "未填写"}</dd>
                </div>
              </dl>
            </ReferenceCard>
            <ReferenceCard title="正文摘要">
              <TextArea label="摘要" value={workbench.contentForm.chapter_summary} onChange={(value) => setContentFormValue("chapter_summary", value, workbench.setContentForm)} />
            </ReferenceCard>
            <ReferenceCard title="前文参考">
              <p>{workbench.previousEpisodeSummary}</p>
              {workbench.selectedEpisodeNo > 1 ? <p className="hint">来源：第 {workbench.selectedEpisodeNo - 1} 集正文摘要。</p> : null}
            </ReferenceCard>
          </aside>

          <section className="episode-paper-editor" aria-label="正文编辑区">
            <div className="paper-editor-heading">
              <div>
                <h3>正文编辑区</h3>
              </div>
              <div className="paper-editor-actions">
                <span className="word-count-row">{workbench.contentWordCount} 字</span>
                <SimpleSelect
                  aria-label="正文状态"
                  value={workbench.contentForm.status}
                  onValueChange={(value) => setContentFormValue("status", value as ProjectArtifactStatus, workbench.setContentForm)}
                  options={[
                    { label: "草稿", value: "draft" },
                    { label: "已确认", value: "confirmed" },
                    { label: "需要检查", value: "needs_review" }
                  ]}
                />
                <Button className="button" type="submit" disabled={workbench.isSaving}>
                  {workbench.isSaving ? "保存中..." : "保存"}
                </Button>
              </div>
            </div>
            <TextArea label="正文内容" value={workbench.contentForm.detailed_content} onChange={(value) => setContentFormValue("detailed_content", value, workbench.setContentForm)} />
          </section>

          <WritingReferencePanel workbench={workbench} />
        </div>
      </form>
    </section>
  );
}

function WritingReferencePanel({ workbench }: { workbench: ProjectWorkbenchState }) {
  return (
    <aside className="writing-reference-panel" aria-label="正文创作参考面板">
      <div className="reference-tabs" role="tablist" aria-label="参考面板">
        {referenceTabs.map((tab) => (
          <Button
            className={`reference-tab ${workbench.activeReferenceTab === tab.key ? "active" : ""}`}
            type="button"
            variant="ghost"
            key={tab.key}
            onClick={() => workbench.setActiveReferenceTab(tab.key)}
          >
            {tab.label}
          </Button>
        ))}
      </div>
      <div className="reference-tab-panel">
        {workbench.activeReferenceTab === "settings" ? (
          <ReferenceCard title="世界观设定">
            <p>{workbench.worldSnapshots[0] ? worldSnapshotSummary(workbench.worldSnapshots[0]) : "尚未加载项目世界观。"}</p>
            <Button className="reference-link-button" type="button" variant="ghost" onClick={() => workbench.showAiPlaceholder("设定参考")}>
              设定参考
            </Button>
          </ReferenceCard>
        ) : null}
        {workbench.activeReferenceTab === "characters" ? (
          <ReferenceCard title="角色参考">
            {workbench.characterSnapshots.length > 0 ? (
              <ul className="compact-list">
                {workbench.characterSnapshots.slice(0, 8).map((character) => (
                  <li key={character.id}>
                    <strong>{character.name}</strong>
                    <span>{character.role_type}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p>尚未加载项目角色。</p>
            )}
            <Button className="reference-link-button" type="button" variant="ghost" onClick={() => workbench.showAiPlaceholder("角色参考")}>
              角色参考
            </Button>
          </ReferenceCard>
        ) : null}
        {workbench.activeReferenceTab === "style" ? (
          <ReferenceCard title="文风">
            <p>用于沉淀表达偏好、文风规则和参考资料摘要。本阶段只展示入口。</p>
            <Button className="reference-link-button" type="button" variant="ghost" onClick={() => workbench.showAiPlaceholder("文风面板")}>
              文风
            </Button>
          </ReferenceCard>
        ) : null}
        {workbench.activeReferenceTab === "inspiration" ? (
          <ReferenceCard title="灵感">
            <p>用于沉淀可选桥段、冲突点、反转方向和短剧爽点。本阶段只展示入口。</p>
            <Button className="reference-link-button" type="button" variant="ghost" onClick={() => workbench.showAiPlaceholder("灵感面板")}>
              灵感
            </Button>
          </ReferenceCard>
        ) : null}
      </div>
      <ReferenceCard title="质检备注">
        <TextArea label="备注" value={workbench.contentForm.quality_check_notes} onChange={(value) => setContentFormValue("quality_check_notes", value, workbench.setContentForm)} />
        <Button className="reference-link-button" type="button" variant="ghost" onClick={() => workbench.showAiPlaceholder("一致性质检")}>
          一致性质检
        </Button>
      </ReferenceCard>
    </aside>
  );
}
