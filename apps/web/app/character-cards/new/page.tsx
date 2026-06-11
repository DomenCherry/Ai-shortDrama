"use client";

import Link from "next/link";
import { FormEvent, MouseEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { createCharacterCard, generateCharacterTurnaround, uploadCharacterReferenceImage } from "@/lib/api";
import {
  buildTurnaroundPrompt,
  CharacterCardForm,
  CharacterCardFormView,
  emptyCharacterCardForm,
  formToPayload,
  TurnaroundPromptField,
  validateTurnaroundPromptFields,
  validateCharacterCard
} from "../_components/CharacterCardForm";

export default function NewCharacterCardPage() {
  const router = useRouter();
  const [form, setForm] = useState<CharacterCardForm>(emptyCharacterCardForm);
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isUploadingReference, setIsUploadingReference] = useState(false);
  const [isGeneratingTurnaround, setIsGeneratingTurnaround] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [hasManualTurnaroundPromptChange, setHasManualTurnaroundPromptChange] = useState(false);
  const [hasTriedSubmit, setHasTriedSubmit] = useState(false);
  const [pendingLeaveHref, setPendingLeaveHref] = useState("");
  const [isPromptOverwriteOpen, setIsPromptOverwriteOpen] = useState(false);
  const validationError = validateCharacterCard(form);
  const isBusy = isSaving || isUploadingReference || isGeneratingTurnaround;

  const updateField = (field: keyof CharacterCardForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    if (field === "turnaround_prompt") {
      setHasManualTurnaroundPromptChange(true);
    }
    setHasUnsavedChanges(true);
    setError("");
  };

  const guardLeaveToList = (event: MouseEvent<HTMLAnchorElement>) => {
    // 新建页允许直接回到列表，但有未保存内容时必须先让用户确认，避免误丢角色设定。
    if (hasUnsavedChanges) {
      event.preventDefault();
      setPendingLeaveHref(event.currentTarget.getAttribute("href") || "/character-cards");
    }
  };

  const saveCard = async (event: FormEvent) => {
    event.preventDefault();
    setHasTriedSubmit(true);
    setError("");

    if (validationError) {
      return;
    }

    setIsSaving(true);
    try {
      const savedCard = await createCharacterCard(formToPayload(form));
      setHasUnsavedChanges(false);
      router.push(`/character-cards/${savedCard.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "角色卡创建失败");
    } finally {
      setIsSaving(false);
    }
  };

  const uploadReferenceFromNewCard = async (file: File | null) => {
    if (!file) return;
    setHasTriedSubmit(true);
    const fileError = validateReferenceImageFile(file);
    if (fileError) {
      setError(fileError);
      return;
    }
    if (validationError) {
      return;
    }

    setIsUploadingReference(true);
    setError("");
    try {
      const dataUrl = await readFileAsDataUrl(file);
      const savedCard = await createCharacterCard(formToPayload(form));

      try {
        await uploadCharacterReferenceImage(savedCard.id, {
          filename: file.name,
          content_type: file.type,
          data_url: dataUrl
        });
        router.push(`/character-cards/${savedCard.id}?notice=reference_uploaded`);
      } catch (err) {
        const message = err instanceof Error ? err.message : "参考图上传失败，请在详情页重试。";
        router.push(`/character-cards/${savedCard.id}?error=${encodeURIComponent(message)}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "角色卡创建失败，参考图未上传。");
    } finally {
      setIsUploadingReference(false);
    }
  };

  const applyTurnaroundPrompt = () => {
    // 生成提示词只是本地文本辅助动作，不创建角色卡，也不调用图片模型。
    setForm((current) => ({
      ...current,
      turnaround_prompt: buildTurnaroundPrompt(current, hasManualTurnaroundPromptChange)
    }));
    setHasManualTurnaroundPromptChange(false);
    setHasUnsavedChanges(true);
    setError("");
  };

  const generateTurnaroundPrompt = () => {
    const promptError = validateTurnaroundPromptFields(form);
    if (promptError) {
      setError(promptError);
      return;
    }
    if (form.turnaround_prompt.trim() && hasManualTurnaroundPromptChange) {
      setIsPromptOverwriteOpen(true);
      return;
    }

    applyTurnaroundPrompt();
  };

  const generateTurnaroundFromNewCard = async () => {
    setHasTriedSubmit(true);
    if (validationError) {
      return;
    }
    if (!form.visual_description.trim() && !form.image_keywords.trim()) {
      setError("请先填写视觉描述或形象关键词后再生成三视图。");
      return;
    }

    setIsGeneratingTurnaround(true);
    setError("");
    try {
      const savedCard = await createCharacterCard(formToPayload(form));

      try {
        await generateCharacterTurnaround(savedCard.id, form.turnaround_prompt);
        router.push(`/character-cards/${savedCard.id}?notice=turnaround_generated`);
      } catch (err) {
        const message = err instanceof Error ? err.message : "三视图生成失败，请在详情页重试。";
        router.push(`/character-cards/${savedCard.id}?error=${encodeURIComponent(message)}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "角色卡创建失败，三视图未生成。");
    } finally {
      setIsGeneratingTurnaround(false);
    }
  };

  return (
    <div className="stack">
      <ConfirmDialog
        open={Boolean(pendingLeaveHref)}
        title="离开当前页面？"
        description="当前页面有未保存内容，离开后这些角色设定不会保存。"
        confirmLabel="离开"
        onOpenChange={(open) => {
          if (!open) setPendingLeaveHref("");
        }}
        onConfirm={() => {
          const href = pendingLeaveHref;
          setPendingLeaveHref("");
          router.push(href);
        }}
      />
      <ConfirmDialog
        destructive
        open={isPromptOverwriteOpen}
        title="覆盖三视图提示词？"
        description="当前三视图提示词已有手动修改，覆盖后无法自动恢复。"
        confirmLabel="覆盖"
        onOpenChange={setIsPromptOverwriteOpen}
        onConfirm={() => {
          setIsPromptOverwriteOpen(false);
          applyTurnaroundPrompt();
        }}
      />
      <header className="page-header">
        <div>
          <h1 className="page-title">新建角色卡</h1>
          <p className="page-description">创建可在多个短剧项目中复用的人物资产。具体剧情目标、人物关系和冲突会在项目内塑造。</p>
        </div>
        <Button variant="secondary" asChild>
          <Link href="/character-cards" onClick={guardLeaveToList}>返回列表</Link>
        </Button>
      </header>

      <form className="panel stack form-page" onSubmit={saveCard}>
        <div className="section-heading">
          <h2>角色设定</h2>
          {hasUnsavedChanges ? <span className="warning-text">有未保存内容</span> : null}
        </div>

        <CharacterCardFormView form={form} onChange={updateField} hideStatusField />

        <section className="form-section stack">
          <h3>参考图上传</h3>
          <p className="field-hint">
            选择参考图后，系统会先自动保存角色卡草稿，再上传图片并进入详情页。上传成功后该图会作为三视图生成参考。
          </p>
          <div className="field">
            <label>上传参考图</label>
            <Input
              accept="image/png,image/jpeg,image/webp"
              disabled={isBusy}
              type="file"
              onChange={(event) => void uploadReferenceFromNewCard(event.target.files?.[0] ?? null)}
            />
            <span className="field-hint">支持 png、jpg、webp，单张不超过 10MB。</span>
          </div>
          {isUploadingReference ? <div className="hint">正在保存角色卡并上传参考图...</div> : null}
        </section>

        <section className="form-section stack">
          <h3>人物三视图</h3>
          <p className="field-hint">
            先根据当前字段生成可编辑提示词，确认内容后再调用已测试成功的图片生成 API 生成人物三视图。
          </p>
          <TurnaroundPromptField form={form} onChange={updateField} disabled={isBusy} />
          <div className="actions action-wrap">
            <Button variant="secondary" disabled={isBusy} type="button" onClick={generateTurnaroundPrompt}>
              生成提示词
            </Button>
            <Button variant="secondary" disabled={isBusy} type="button" onClick={generateTurnaroundFromNewCard}>
              {isGeneratingTurnaround ? "生成中..." : "生成人物三视图"}
            </Button>
          </div>
        </section>

        {hasTriedSubmit && validationError ? <div className="error">{validationError}</div> : null}
        {error ? <div className="error">{error}</div> : null}

        <div className="actions action-wrap">
          <Button variant="secondary" asChild>
            <Link href="/character-cards" onClick={guardLeaveToList}>取消</Link>
          </Button>
          <Button type="submit" disabled={isBusy}>
            {isSaving ? "保存中..." : "保存角色卡"}
          </Button>
        </div>
      </form>
    </div>
  );
}

function validateReferenceImageFile(file: File) {
  if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) {
    return "请上传 png、jpg 或 webp 格式图片。";
  }
  if (file.size > 10 * 1024 * 1024) {
    return "参考图不能超过 10MB。";
  }
  return "";
}

function readFileAsDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("参考图读取失败，请重新选择文件。"));
    reader.readAsDataURL(file);
  });
}
