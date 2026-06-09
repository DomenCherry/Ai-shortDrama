"use client";

import Link from "next/link";
import type { ProjectWorkbenchState } from "../_hooks/useProjectWorkbench";
import {
  characterSnapshotSummary,
  formatNumber,
  setCharacterSnapshotFormValue,
  setProjectFormValue,
  setWorldSnapshotFormValue,
  worldSnapshotSummary
} from "../_utils/workbenchForms";
import { AssetDrawer, AssetSection, NumberInput, TextArea, TextInput } from "./shared";

export function ProjectAssetsModule({ workbench }: { workbench: ProjectWorkbenchState }) {
  const project = workbench.project;
  if (!project || workbench.isLandingMode) return null;

  return (
    <>
      {workbench.activeStage === "settings" ? <ProjectSettingsPanel workbench={workbench} /> : null}
      {workbench.activeStage === "assets" ? <ProjectAssetPanel workbench={workbench} /> : null}
    </>
  );
}

function ProjectSettingsPanel({ workbench }: { workbench: ProjectWorkbenchState }) {
  return (
    <form className="panel stack" onSubmit={workbench.saveProject}>
      <div className="section-heading">
        <h2>项目设定</h2>
        <button className="button secondary" type="button" onClick={workbench.resetProjectForm} disabled={workbench.isSaving}>
          还原
        </button>
      </div>
      <TextArea label="创意描述" value={workbench.projectForm.idea} onChange={(value) => setProjectFormValue("idea", value, workbench.setProjectForm)} />
      <div className="grid-2">
        <TextInput label="项目名称" value={workbench.projectForm.title} onChange={(value) => setProjectFormValue("title", value, workbench.setProjectForm)} />
        <TextInput label="目标平台" value={workbench.projectForm.target_platform} onChange={(value) => setProjectFormValue("target_platform", value, workbench.setProjectForm)} />
        <TextInput label="题材类型" value={workbench.projectForm.genre} onChange={(value) => setProjectFormValue("genre", value, workbench.setProjectForm)} />
        <TextInput label="目标受众" value={workbench.projectForm.target_audience} onChange={(value) => setProjectFormValue("target_audience", value, workbench.setProjectForm)} />
        <TextInput label="内容风格" value={workbench.projectForm.style} onChange={(value) => setProjectFormValue("style", value, workbench.setProjectForm)} />
        <TextInput label="备注" value={workbench.projectForm.remark} onChange={(value) => setProjectFormValue("remark", value, workbench.setProjectForm)} />
      </div>
      <div className="grid-2">
        <NumberInput label="集数" min="1" step="1" value={workbench.projectForm.episode_count} onChange={(value) => setProjectFormValue("episode_count", value, workbench.setProjectForm)} />
        <NumberInput label="单集时长（分钟）" min="0.1" max="2" step="0.1" value={workbench.projectForm.episode_duration} onChange={(value) => setProjectFormValue("episode_duration", value, workbench.setProjectForm)} />
      </div>
      <div className="summary-box">
        <strong>总时长：</strong>
        {Number.isFinite(workbench.totalDuration) ? `${formatNumber(workbench.totalDuration)} 分钟` : "请填写集数和单集时长"}
        {Number.isFinite(workbench.episodeDuration) && workbench.episodeDuration > 0 ? (
          <span className="hint">，单集约 {formatNumber(workbench.episodeDuration * 60)} 秒</span>
        ) : null}
      </div>
      {workbench.durationChanged ? <div className="warning-text">修改集数或单集时长会让故事文本和短剧制作已有内容进入需要检查状态。</div> : null}
      {workbench.validationError ? <div className="error">{workbench.validationError}</div> : null}
      <div className="actions">
        <button className="button" type="submit" disabled={workbench.isSaving || Boolean(workbench.validationError)}>
          {workbench.isSaving ? "保存中..." : "保存项目设定"}
        </button>
      </div>
    </form>
  );
}

function ProjectAssetPanel({ workbench }: { workbench: ProjectWorkbenchState }) {
  return (
    <>
      <div className="grid-2">
        <WorldSnapshotSection workbench={workbench} />
        <CharacterSnapshotSection workbench={workbench} />
      </div>
      <WorldPickerDrawer workbench={workbench} />
      <CharacterPickerDrawer workbench={workbench} />
    </>
  );
}

function WorldSnapshotSection({ workbench }: { workbench: ProjectWorkbenchState }) {
  return (
    <AssetSection
      title="项目世界观"
      linkHref="/world-books"
      linkLabel="前往世界观库"
      isLoading={workbench.isLoadingAssets}
      emptyText="尚未加载世界观。点击下方按钮从世界观库中选择并加载。"
      onPick={workbench.openWorldPicker}
      pickLabel="加载世界观"
      pickDisabled={workbench.worldSnapshots.length > 0}
    >
      {workbench.worldSnapshots.map((snapshot) => (
        <article className="asset-card" key={snapshot.id}>
          <div className="asset-card-main">
            <div className="asset-card-title">
              <strong>{snapshot.name}</strong>
              <span className="status-badge status-active">已加载 v{snapshot.source_version}</span>
            </div>
            <div className="hint">{snapshot.genre}</div>
            <p>{worldSnapshotSummary(snapshot)}</p>
            <p className="hint">加载时间：{new Date(snapshot.loaded_at).toLocaleString()}</p>
          </div>
          <div className="asset-card-actions">
            <button className="button secondary" type="button" onClick={() => workbench.startEditingWorldSnapshot(snapshot)}>
              编辑项目世界观
            </button>
            <button
              className="button danger"
              type="button"
              onClick={() => void workbench.removeWorldSnapshot(snapshot)}
              disabled={workbench.removingSnapshotId === snapshot.id}
            >
              {workbench.removingSnapshotId === snapshot.id ? "移除中..." : "从项目移除"}
            </button>
          </div>
          {workbench.editingWorldSnapshotId === snapshot.id ? (
            <form className="form-section stack" onSubmit={workbench.saveWorldSnapshot}>
              <div className="warning-text">此处只修改当前项目世界观，不会修改世界观库原始内容。</div>
              <div className="grid-2">
                <TextInput label="项目世界观名称" value={workbench.worldSnapshotForm.name} onChange={(value) => setWorldSnapshotFormValue("name", value, workbench.setWorldSnapshotForm)} />
                <TextInput label="题材类型" value={workbench.worldSnapshotForm.genre} onChange={(value) => setWorldSnapshotFormValue("genre", value, workbench.setWorldSnapshotForm)} />
                <TextArea label="基础设定快照" value={workbench.worldSnapshotForm.snapshot_content} onChange={(value) => setWorldSnapshotFormValue("snapshot_content", value, workbench.setWorldSnapshotForm)} />
                <TextArea label="条目快照" value={workbench.worldSnapshotForm.entry_snapshot_content} onChange={(value) => setWorldSnapshotFormValue("entry_snapshot_content", value, workbench.setWorldSnapshotForm)} />
              </div>
              <div className="actions">
                <button className="button secondary" type="button" onClick={workbench.cancelWorldSnapshotEdit} disabled={workbench.savingSnapshotId === snapshot.id}>
                  取消
                </button>
                <button className="button" type="submit" disabled={workbench.savingSnapshotId === snapshot.id}>
                  {workbench.savingSnapshotId === snapshot.id ? "保存中..." : "保存项目世界观"}
                </button>
              </div>
            </form>
          ) : null}
        </article>
      ))}
    </AssetSection>
  );
}

function CharacterSnapshotSection({ workbench }: { workbench: ProjectWorkbenchState }) {
  return (
    <AssetSection
      title="项目角色"
      linkHref="/character-cards"
      linkLabel="前往角色卡库"
      isLoading={workbench.isLoadingAssets}
      emptyText="尚未加载角色。点击下方按钮从角色卡库中选择并加载。"
      onPick={workbench.openCharacterPicker}
      pickLabel="加载角色"
    >
      {workbench.characterSnapshots.map((snapshot) => (
        <article className="asset-card" key={snapshot.id}>
          <div className="asset-card-main">
            <div className="asset-card-title">
              <strong>{snapshot.name}</strong>
              <span className="status-badge status-active">已加载 v{snapshot.source_version}</span>
            </div>
            <div className="hint">
              {snapshot.gender} · {snapshot.role_type}
            </div>
            <p>{snapshot.visual_description || characterSnapshotSummary(snapshot)}</p>
            <p className="hint">加载时间：{new Date(snapshot.loaded_at).toLocaleString()}</p>
          </div>
          <div className="asset-card-actions">
            <button className="button secondary" type="button" onClick={() => workbench.startEditingCharacterSnapshot(snapshot)}>
              编辑项目角色
            </button>
            <button
              className="button danger"
              type="button"
              onClick={() => void workbench.removeCharacterSnapshot(snapshot)}
              disabled={workbench.removingSnapshotId === snapshot.id}
            >
              {workbench.removingSnapshotId === snapshot.id ? "移除中..." : "从项目移除"}
            </button>
          </div>
          {workbench.editingCharacterSnapshotId === snapshot.id ? (
            <form className="form-section stack" onSubmit={workbench.saveCharacterSnapshot}>
              <div className="warning-text">此处只修改当前项目角色，不会修改角色卡库原始内容。</div>
              <div className="grid-2">
                <TextInput label="项目角色名" value={workbench.characterSnapshotForm.name} onChange={(value) => setCharacterSnapshotFormValue("name", value, workbench.setCharacterSnapshotForm)} />
                <div className="field">
                  <label>性别</label>
                  <select
                    value={workbench.characterSnapshotForm.gender}
                    onChange={(event) => setCharacterSnapshotFormValue("gender", event.target.value as "男" | "女", workbench.setCharacterSnapshotForm)}
                  >
                    <option value="女">女</option>
                    <option value="男">男</option>
                  </select>
                </div>
                <TextInput label="人物原型 / 项目定位" value={workbench.characterSnapshotForm.role_type} onChange={(value) => setCharacterSnapshotFormValue("role_type", value, workbench.setCharacterSnapshotForm)} />
                <TextArea label="项目角色设定快照" value={workbench.characterSnapshotForm.snapshot_content} onChange={(value) => setCharacterSnapshotFormValue("snapshot_content", value, workbench.setCharacterSnapshotForm)} />
                <TextArea label="项目内视觉描述" value={workbench.characterSnapshotForm.visual_description} onChange={(value) => setCharacterSnapshotFormValue("visual_description", value, workbench.setCharacterSnapshotForm)} />
                <TextInput label="参考图 URL" value={workbench.characterSnapshotForm.reference_image_url} onChange={(value) => setCharacterSnapshotFormValue("reference_image_url", value, workbench.setCharacterSnapshotForm)} />
                <TextInput label="参考图本地路径" value={workbench.characterSnapshotForm.reference_local_path} onChange={(value) => setCharacterSnapshotFormValue("reference_local_path", value, workbench.setCharacterSnapshotForm)} />
              </div>
              <div className="actions">
                <button className="button secondary" type="button" onClick={workbench.cancelCharacterSnapshotEdit} disabled={workbench.savingSnapshotId === snapshot.id}>
                  取消
                </button>
                <button className="button" type="submit" disabled={workbench.savingSnapshotId === snapshot.id}>
                  {workbench.savingSnapshotId === snapshot.id ? "保存中..." : "保存项目角色"}
                </button>
              </div>
            </form>
          ) : null}
        </article>
      ))}
    </AssetSection>
  );
}

function WorldPickerDrawer({ workbench }: { workbench: ProjectWorkbenchState }) {
  return (
    <AssetDrawer title="选择世界观" isOpen={workbench.showWorldPicker} onClose={() => workbench.setShowWorldPicker(false)}>
      {workbench.isLoadingPicker ? (
        <div className="empty-state">正在加载可用世界观...</div>
      ) : workbench.availableWorlds.length === 0 ? (
        <div className="empty-state">
          没有可用的世界观。
          <Link href="/world-books/new" className="button secondary" style={{ marginTop: "0.5rem", display: "inline-block" }}>
            创建世界观
          </Link>
        </div>
      ) : (
        <>
          {workbench.worldSnapshots.length > 0 ? (
            <div className="warning-text">当前项目已加载世界观，每个项目只能加载一个世界观。</div>
          ) : (
            <div className="drawer-selection-hint">请选择一个世界观，然后点击底部「加载」按钮。</div>
          )}
          <div className="asset-list asset-drawer-list">
            {workbench.availableWorlds.map((wb) => {
              const hasProjectWorld = workbench.worldSnapshots.length > 0;
              const isLoaded = workbench.loadedWorldIds.has(wb.id);
              const isDisabled = hasProjectWorld || isLoaded;
              const isSelected = workbench.selectedWorldId === wb.id;
              return (
                <label
                  className={`drawer-asset-item ${isSelected ? "drawer-item-selected" : ""} ${isDisabled ? "drawer-item-disabled" : ""}`}
                  key={wb.id}
                >
                  <div className="drawer-asset-item-header">
                    <input
                      type="radio"
                      name="world-pick"
                      checked={isSelected}
                      disabled={isDisabled}
                      onChange={() => workbench.setSelectedWorldId(wb.id)}
                    />
                    <strong>{wb.name}</strong>
                    {isLoaded ? (
                      <span className="status-badge status-active">已加载</span>
                    ) : hasProjectWorld ? (
                      <span className="status-badge status-draft">不可加载</span>
                    ) : (
                      <span className="status-badge status-draft">可用</span>
                    )}
                  </div>
                  <div className="hint">{wb.genre} · v{wb.version}</div>
                  <p>{wb.summary || wb.world_rules || "无简介"}</p>
                </label>
              );
            })}
          </div>
        </>
      )}
      {!workbench.isLoadingPicker && workbench.availableWorlds.length > 0 && (
        <div className="asset-drawer-footer">
          <button className="button secondary" type="button" onClick={() => workbench.setShowWorldPicker(false)}>
            取消
          </button>
          <button
            className="button"
            type="button"
            disabled={!workbench.selectedWorldId || workbench.loadingAssetId !== "" || workbench.worldSnapshots.length > 0}
            onClick={() => void workbench.handleLoadWorld()}
          >
            {workbench.loadingAssetId ? "加载中..." : `加载${workbench.selectedWorldId ? "" : "世界观"}`}
          </button>
        </div>
      )}
      <div className="hint" style={{ textAlign: "center" }}>
        <Link href="/world-books">前往世界观库管理</Link>
      </div>
    </AssetDrawer>
  );
}

function CharacterPickerDrawer({ workbench }: { workbench: ProjectWorkbenchState }) {
  return (
    <AssetDrawer title="选择角色卡" isOpen={workbench.showCharacterPicker} onClose={() => workbench.setShowCharacterPicker(false)}>
      {workbench.isLoadingPicker ? (
        <div className="empty-state">正在加载可用角色卡...</div>
      ) : workbench.availableCharacters.length === 0 ? (
        <div className="empty-state">
          没有可用的角色卡。
          <Link href="/character-cards/new" className="button secondary" style={{ marginTop: "0.5rem", display: "inline-block" }}>
            创建角色卡
          </Link>
        </div>
      ) : (
        <>
          <div className="drawer-selection-hint">
            已选择 {workbench.selectedCharacterIds.size} 个角色，选择完毕后点击底部「加载」按钮。
          </div>
          <div className="asset-list asset-drawer-list">
            {workbench.availableCharacters.map((cc) => {
              const isLoaded = workbench.loadedCharacterIds.has(cc.id);
              const isSelected = workbench.selectedCharacterIds.has(cc.id);
              const isDisabled = isLoaded;
              return (
                <label
                  className={`drawer-asset-item ${isSelected ? "drawer-item-selected" : ""} ${isDisabled ? "drawer-item-disabled" : ""}`}
                  key={cc.id}
                >
                  <div className="drawer-asset-item-header">
                    <input
                      type="checkbox"
                      checked={isSelected || isLoaded}
                      disabled={isDisabled}
                      onChange={() => {
                        workbench.setSelectedCharacterIds((prev) => {
                          const next = new Set(prev);
                          if (next.has(cc.id)) {
                            next.delete(cc.id);
                          } else {
                            next.add(cc.id);
                          }
                          return next;
                        });
                      }}
                    />
                    <strong>{cc.name}</strong>
                    {isLoaded ? (
                      <span className="status-badge status-active">已加载</span>
                    ) : (
                      <span className="status-badge status-draft">可用</span>
                    )}
                  </div>
                  <div className="hint">{cc.gender} · {cc.role_type} · v{cc.version}</div>
                  <p>{cc.identity || cc.background || "无简介"}</p>
                </label>
              );
            })}
          </div>
        </>
      )}
      {!workbench.isLoadingPicker && workbench.availableCharacters.length > 0 && (
        <div className="asset-drawer-footer">
          <button className="button secondary" type="button" onClick={() => workbench.setShowCharacterPicker(false)}>
            取消
          </button>
          <button
            className="button"
            type="button"
            disabled={workbench.selectedCharacterIds.size === 0 || workbench.isBatchLoading}
            onClick={() => void workbench.handleLoadCharacters()}
          >
            {workbench.isBatchLoading ? "加载中..." : `加载${workbench.selectedCharacterIds.size > 0 ? ` (${workbench.selectedCharacterIds.size})` : ""}`}
          </button>
        </div>
      )}
      <div className="hint" style={{ textAlign: "center" }}>
        <Link href="/character-cards">前往角色卡库管理</Link>
      </div>
    </AssetDrawer>
  );
}
