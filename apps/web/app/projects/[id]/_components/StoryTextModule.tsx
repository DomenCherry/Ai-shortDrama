"use client";

import Link from "next/link";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { SimpleSelect } from "@/components/ui/simple-select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import type { ProjectArtifactStatus } from "@/lib/api";
import type { ProjectWorkbenchState } from "../_hooks/useProjectWorkbench";
import {
  setContentFormValue,
  setEpisodeFormValue,
  setStoryFormValue,
  worldSnapshotSummary
} from "../_utils/workbenchForms";
import { saveStoryOutlineAssistDraft } from "../_utils/storyOutlineAssistDraft";
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
          <Button className="compact-action" variant="secondary" asChild>
            <Link
              href={`/projects/${workbench.projectId}/story-outline/assist`}
              onClick={() => saveStoryOutlineAssistDraft(workbench.projectId, workbench.storyForm)}
            >
              AI协助
            </Link>
          </Button>
          <Button className="compact-action" variant="secondary" asChild>
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
          <Button type="submit" disabled={workbench.isSaving}>
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
            <Button type="submit" disabled={workbench.isSaving}>
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
            <EpisodePicker
              episodeCount={project.episode_count}
              value={workbench.selectedEpisodeNo}
              onChange={workbench.setSelectedEpisodeNo}
              disabled={workbench.isGeneratingContent}
            />
            <div className="episode-index-list">
              {workbench.episodeRows.map((row) => (
                <Button
                  className={`episode-index-item ${workbench.selectedEpisodeNo === row.episodeNo ? "active" : ""}`}
                  type="button"
                  variant="ghost"
                  disabled={workbench.isGeneratingContent}
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
                <h3>{workbench.contentEditorMode === "candidate" ? "AI 候选稿" : "正文编辑区"}</h3>
              </div>
              <div className="paper-editor-actions">
                <span className="word-count-row">
                  {workbench.contentEditorMode === "candidate"
                    ? countWritingCharacters(workbench.contentGenerationDraft)
                    : workbench.contentWordCount}{" "}
                  字
                </span>
                {workbench.contentEditorMode === "current" ? (
                  <>
                    <SimpleSelect
                      aria-labelledby="episode-content-status-label"
                      value={workbench.contentForm.status}
                      onValueChange={(value) => setContentFormValue("status", value as ProjectArtifactStatus, workbench.setContentForm)}
                      options={[
                        { label: "草稿", value: "draft" },
                        { label: "已确认", value: "confirmed" },
                        { label: "需要检查", value: "needs_review" }
                      ]}
                    />
                    <span className="sr-only" id="episode-content-status-label">正文状态</span>
                    <Button type="submit" disabled={workbench.isSaving}>
                      {workbench.isSaving ? "保存中..." : "保存正文"}
                    </Button>
                  </>
                ) : null}
              </div>
            </div>

            {workbench.showContentCreator ? <EpisodeContentCreator workbench={workbench} /> : null}

            <Tabs
              value={workbench.contentEditorMode}
              onValueChange={(value) => workbench.setContentEditorMode(value as "current" | "candidate")}
            >
              <TabsList aria-label="正文版本视图">
                <TabsTrigger value="current">当前正文</TabsTrigger>
                <TabsTrigger value="candidate" disabled={!workbench.activeContentGeneration && !workbench.isGeneratingContent}>
                  AI 候选
                </TabsTrigger>
              </TabsList>
              <TabsContent value="current">
                <TextArea
                  label="正文内容"
                  value={workbench.contentForm.detailed_content}
                  onChange={(value) => setContentFormValue("detailed_content", value, workbench.setContentForm)}
                />
              </TabsContent>
              <TabsContent value="candidate">
                {workbench.isGeneratingContent ? (
                  <div className="generation-loading" role="status" aria-live="polite">
                    <strong>正在生成第 {workbench.selectedEpisodeNo} 集候选稿</strong>
                    <span>模型正在读取大纲、世界观、角色和前文摘要，通常需要 20–60 秒。</span>
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-11/12" />
                    <Skeleton className="h-4 w-4/5" />
                  </div>
                ) : workbench.activeContentGeneration ? (
                  <div className="candidate-editor">
                    <div className="candidate-meta">
                      <Badge variant="secondary">{generationStatusLabel(workbench.activeContentGeneration.status)}</Badge>
                      <span>{formatGenerationTime(workbench.activeContentGeneration.created_at)}</span>
                      {workbench.activeContentGeneration.model_name ? <span>{workbench.activeContentGeneration.model_name}</span> : null}
                    </div>
                    <label htmlFor="episode-content-candidate">候选正文</label>
                    <Textarea
                      id="episode-content-candidate"
                      value={workbench.contentGenerationDraft}
                      readOnly={workbench.activeContentGeneration.status !== "candidate"}
                      onChange={(event) => workbench.setContentGenerationDraft(event.target.value)}
                    />
                    {workbench.activeContentGeneration.status === "candidate" ? (
                      <div className="candidate-actions">
                        <Button
                          type="button"
                          variant="secondary"
                          disabled={workbench.isSavingContentGeneration || !workbench.contentGenerationDraft.trim()}
                          onClick={() => void workbench.saveContentGenerationDraft()}
                        >
                          {workbench.isSavingContentGeneration ? "保存中..." : "保存候选修改"}
                        </Button>
                        <Button
                          type="button"
                          disabled={workbench.isAdoptingContentGeneration || !workbench.contentGenerationDraft.trim()}
                          onClick={() => void workbench.adoptContentGeneration()}
                        >
                          {workbench.isAdoptingContentGeneration ? "采用中..." : "采用为正文"}
                        </Button>
                        <Button
                          type="button"
                          variant="secondary"
                          disabled={workbench.isGeneratingContent}
                          onClick={() => void workbench.generateEpisodeContentCandidate()}
                        >
                          重新生成
                        </Button>
                        <Button type="button" variant="ghost" onClick={() => void workbench.discardContentGeneration()}>
                          放弃候选
                        </Button>
                      </div>
                    ) : (
                      <p className="hint">这是历史版本，只能查看，不能再次采用或编辑。</p>
                    )}
                  </div>
                ) : (
                  <p className="hint">尚未生成候选稿。</p>
                )}
              </TabsContent>
            </Tabs>
          </section>

          <WritingReferencePanel workbench={workbench} />
        </div>
      </form>
    </section>
  );
}

function EpisodeContentCreator({ workbench }: { workbench: ProjectWorkbenchState }) {
  const project = workbench.project;
  if (!project) return null;
  const duration = workbench.selectedEpisodeOutline?.duration_minutes || project.episode_duration || 1;
  const targetMin = Math.max(60, Math.round(duration * 600));
  const targetMax = Math.max(targetMin, Math.round(duration * 900));
  const historyOptions = workbench.episodeContentGenerations.map((generation) => ({
    value: generation.id,
    label: `${formatGenerationTime(generation.created_at)} · ${generationStatusLabel(generation.status)}`
  }));

  return (
    <section className="content-generation-composer" aria-labelledby="content-generation-title">
      <div className="content-generation-heading">
        <div>
          <h4 id="content-generation-title">生成第 {workbench.selectedEpisodeNo} 集候选稿</h4>
          <p>AI 结果会先保存为候选版本，不会直接覆盖当前正文。</p>
        </div>
        <Button type="button" variant="ghost" disabled={workbench.isGeneratingContent} onClick={() => workbench.setShowContentCreator(false)}>
          收起
        </Button>
      </div>

      <div className="generation-context-list" aria-label="本次生成上下文">
        <Badge variant="secondary">整体大纲 {workbench.storyOutline ? "已读取" : "未填写"}</Badge>
        <Badge variant="secondary">本集大纲 已读取</Badge>
        <Badge variant="secondary">世界观 {workbench.worldSnapshots.length} 份</Badge>
        <Badge variant="secondary">角色 {workbench.characterSnapshots.length} 个</Badge>
        <Badge variant="secondary">
          前文摘要 {workbench.selectedEpisodeNo === 1 ? "首集无需" : workbench.previousEpisodeSummary.includes("尚未填写") ? "未填写" : "已读取"}
        </Badge>
        <Badge variant="outline">目标约 {targetMin}–{targetMax} 字</Badge>
      </div>

      {!workbench.canGenerateEpisodeContent ? (
        <Alert variant="destructive">
          <AlertTitle>当前集缺少可用大纲</AlertTitle>
          <AlertDescription>请先填写并保存本集标题、梗概、钩子、冲突、反转或悬念，再生成正文。</AlertDescription>
        </Alert>
      ) : null}

      <div className="generation-instruction-field">
        <label htmlFor="episode-content-instruction">本次创作要求（可选）</label>
        <Textarea
          id="episode-content-instruction"
          value={workbench.contentGenerationInstruction}
          disabled={workbench.isGeneratingContent}
          placeholder="例如：加强女主发现证据时的压迫感，结尾停在门外脚步声响起。"
          onChange={(event) => workbench.setContentGenerationInstruction(event.target.value)}
        />
        <span className="hint">补充本次节奏、情绪或桥段要求；项目设定和本集关键节点仍会优先遵守。</span>
      </div>

      <div className="content-generation-footer">
        {historyOptions.length > 0 ? (
          <div className="generation-history-field">
            <label id="generation-history-label">最近生成</label>
            <SimpleSelect
              aria-labelledby="generation-history-label"
              value={workbench.activeContentGeneration?.id ?? ""}
              options={historyOptions}
              onValueChange={workbench.selectContentGeneration}
              placeholder="选择历史版本"
            />
          </div>
        ) : <span className="hint">当前集还没有生成记录。</span>}
        <Button
          type="button"
          disabled={!workbench.canGenerateEpisodeContent || workbench.isGeneratingContent}
          onClick={() => void workbench.generateEpisodeContentCandidate()}
        >
          {workbench.isGeneratingContent ? "正在生成候选稿..." : "生成候选稿"}
        </Button>
      </div>
    </section>
  );
}

function countWritingCharacters(value: string) {
  return Array.from(value).filter((character) => !/\s/.test(character)).length;
}

function generationStatusLabel(status: "candidate" | "adopted" | "discarded") {
  if (status === "adopted") return "已采用";
  if (status === "discarded") return "已放弃";
  return "候选中";
}

function formatGenerationTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).format(new Date(value));
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
            <Button className="reference-link-action" type="button" variant="ghost" onClick={() => workbench.showAiPlaceholder("设定参考")}>
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
            <Button className="reference-link-action" type="button" variant="ghost" onClick={() => workbench.showAiPlaceholder("角色参考")}>
              角色参考
            </Button>
          </ReferenceCard>
        ) : null}
        {workbench.activeReferenceTab === "style" ? (
          <ReferenceCard title="文风">
            <p>用于沉淀表达偏好、文风规则和参考资料摘要。本阶段只展示入口。</p>
            <Button className="reference-link-action" type="button" variant="ghost" onClick={() => workbench.showAiPlaceholder("文风面板")}>
              文风
            </Button>
          </ReferenceCard>
        ) : null}
        {workbench.activeReferenceTab === "inspiration" ? (
          <ReferenceCard title="灵感">
            <p>用于沉淀可选桥段、冲突点、反转方向和短剧爽点。本阶段只展示入口。</p>
            <Button className="reference-link-action" type="button" variant="ghost" onClick={() => workbench.showAiPlaceholder("灵感面板")}>
              灵感
            </Button>
          </ReferenceCard>
        ) : null}
      </div>
      <ReferenceCard title="质检备注">
        <TextArea label="备注" value={workbench.contentForm.quality_check_notes} onChange={(value) => setContentFormValue("quality_check_notes", value, workbench.setContentForm)} />
        <Button className="reference-link-action" type="button" variant="ghost" onClick={() => workbench.showAiPlaceholder("一致性质检")}>
          一致性质检
        </Button>
      </ReferenceCard>
    </aside>
  );
}
