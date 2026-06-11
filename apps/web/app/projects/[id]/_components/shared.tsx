"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import type { ProjectArtifactStatus, ProjectCharacterSnapshot, ProjectEpisodeOutline, ProjectWorldSnapshot } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetTitle
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { artifactStatusClass, artifactStatusLabel, formatNumber } from "../_utils/workbenchForms";

export function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-item">
      <span className="hint">{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function WorkspaceEntryCard({
  title,
  description,
  metrics,
  isActive,
  href,
  onClick
}: {
  title: string;
  description: string;
  metrics: string[];
  isActive: boolean;
  href?: string;
  onClick?: () => void;
}) {
  const content = (
    <>
      <span className="workspace-entry-title">{title}</span>
      <span className="workspace-entry-description">{description}</span>
      <span className="workspace-entry-metrics">
        {metrics.map((metric) => (
          <span key={metric}>{metric}</span>
        ))}
      </span>
    </>
  );

  if (href) {
    return (
      <Link className={`workspace-entry-card ${isActive ? "active" : ""}`} href={href}>
        {content}
      </Link>
    );
  }

  return (
    <Button className={`workspace-entry-card ${isActive ? "active" : ""}`} type="button" variant="ghost" onClick={onClick}>
      {content}
    </Button>
  );
}

export function SectionTitle({ title, status }: { title: string; status: ProjectArtifactStatus }) {
  return (
    <div className="section-heading">
      <h2>{title}</h2>
      <ArtifactStatusBadge status={status} />
    </div>
  );
}

export function ArtifactStatusBadge({ status }: { status: ProjectArtifactStatus }) {
  return <Badge className={`status-badge ${artifactStatusClass(status)}`}>{artifactStatusLabel(status)}</Badge>;
}

export function ProductionContextSummary({
  worldSnapshots,
  characterSnapshots,
  storyOutlineStatus,
  episodeOutline,
  episodeContentStatus,
  projectId
}: {
  worldSnapshots: ProjectWorldSnapshot[];
  characterSnapshots: ProjectCharacterSnapshot[];
  storyOutlineStatus: ProjectArtifactStatus;
  episodeOutline: ProjectEpisodeOutline | null;
  episodeContentStatus: ProjectArtifactStatus;
  projectId: string;
}) {
  const hasNeedsReview =
    storyOutlineStatus === "needs_review" ||
    episodeOutline?.status === "needs_review" ||
    episodeContentStatus === "needs_review";
  const hasMissingContext = worldSnapshots.length === 0 || characterSnapshots.length === 0 || !episodeOutline;

  return (
    <section className="readonly-context readonly-context-compact" aria-label="短剧制作沿用上下文">
      <details>
        <summary>
          <span className="readonly-context-title">沿用上游上下文</span>
          <span className="hint">世界观 {worldSnapshots[0]?.name || "未加载"} · 角色 {characterSnapshots.length} 个 · 正文 {artifactStatusLabel(episodeContentStatus)}</span>
        </summary>
        <p className="hint">短剧制作只读取项目资产和故事文本；如需调整世界观、角色或单集故事正文，请回到对应入口修改。</p>
        <div className="readonly-context-grid">
          <Metric label="世界观" value={worldSnapshots[0]?.name || "未加载"} />
          <Metric label="角色" value={`${characterSnapshots.length} 个`} />
          <Metric label="整体大纲" value={artifactStatusLabel(storyOutlineStatus)} />
          <Metric label="当前分集大纲" value={episodeOutline ? artifactStatusLabel(episodeOutline.status) : "草稿"} />
          <Metric label="当前单集正文" value={artifactStatusLabel(episodeContentStatus)} />
        </div>
        <div className="actions">
          <Button variant="secondary" asChild>
            <Link href={`/projects/${projectId}/assets`}>回到项目资料 / 资产</Link>
          </Button>
          <Button variant="secondary" asChild>
            <Link href={`/projects/${projectId}/story-text?stage=content`}>回到单集故事正文</Link>
          </Button>
        </div>
      </details>
      {hasNeedsReview ? <div className="warning-text">上游故事文本存在需要检查内容，建议确认后再继续短剧制作。</div> : null}
      {hasMissingContext ? <div className="warning-text">项目资产或当前集故事文本尚未完整，短剧制作结果可能缺少连续性依据。</div> : null}
    </section>
  );
}

export function ReferenceCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="reference-card">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

export function AssetSection({
  title,
  linkHref,
  linkLabel,
  isLoading,
  emptyText,
  onPick,
  pickLabel,
  pickDisabled,
  children
}: {
  title: string;
  linkHref: string;
  linkLabel: string;
  isLoading: boolean;
  emptyText: string;
  onPick?: () => void;
  pickLabel?: string;
  pickDisabled?: boolean;
  children: ReactNode;
}) {
  const childArray = Array.isArray(children) ? children : [children];
  return (
    <section className="panel stack">
      <div className="section-heading">
        <h2>{title}</h2>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {onPick && pickLabel ? (
            <Button type="button" onClick={onPick} disabled={pickDisabled}>
              {pickLabel}
            </Button>
          ) : null}
          <Button variant="secondary" asChild>
            <Link href={linkHref}>{linkLabel}</Link>
          </Button>
        </div>
      </div>
      {isLoading ? (
        <div className="empty-state">正在加载项目资产...</div>
      ) : childArray.length === 0 ? (
        <div className="empty-state">{emptyText}</div>
      ) : (
        <div className="asset-list asset-list-wide">{children}</div>
      )}
    </section>
  );
}

export function AssetDrawer({
  title,
  isOpen,
  onClose,
  children
}: {
  title: string;
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
}) {
  if (!isOpen) return null;

  return (
    <Sheet open={isOpen} onOpenChange={(open) => {
      if (!open) onClose();
    }}>
      <SheetContent className="w-[min(560px,calc(100vw-32px))] max-w-none gap-0 p-0 sm:max-w-none" showCloseButton={false}>
        <div className="asset-drawer-header">
          <SheetTitle id="asset-drawer-title">{title}</SheetTitle>
          <Button variant="secondary" type="button" onClick={onClose}>
            关闭
          </Button>
        </div>
        <div className="asset-drawer-body">{children}</div>
      </SheetContent>
    </Sheet>
  );
}

export function EpisodePicker({ episodeCount, value, onChange }: { episodeCount: number; value: number; onChange: (value: number) => void }) {
  return (
    <div className="field compact-field">
      <label>当前集数</label>
      <Select value={String(value)} onValueChange={(nextValue) => onChange(Number(nextValue))}>
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
        {Array.from({ length: episodeCount }, (_, index) => index + 1).map((episodeNo) => (
          <SelectItem value={String(episodeNo)} key={episodeNo}>
            第 {episodeNo} 集
          </SelectItem>
        ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export function TextInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div className="field">
      <label>{label}</label>
      <Input value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

export function NumberInput({
  label,
  value,
  onChange,
  min,
  max,
  step
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  min?: string;
  max?: string;
  step?: string;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      <Input type="number" min={min} max={max} step={step} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

export function TextArea({
  label,
  value,
  placeholder,
  onChange
}: {
  label: string;
  value: string;
  placeholder?: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      <Textarea value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

export function StatusSelect({ value, onChange }: { value: ProjectArtifactStatus; onChange: (value: ProjectArtifactStatus) => void }) {
  return (
    <div className="field compact-field">
      <label>状态</label>
      <Select value={value} onValueChange={(nextValue) => onChange(nextValue as ProjectArtifactStatus)}>
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="draft">草稿</SelectItem>
          <SelectItem value="confirmed">已确认</SelectItem>
          <SelectItem value="needs_review">需要检查</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}

export { formatNumber };
