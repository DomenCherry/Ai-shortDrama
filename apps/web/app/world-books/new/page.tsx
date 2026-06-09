"use client";

import Link from "next/link";
import { FormEvent, MouseEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { createWorldBook } from "@/lib/api";
import {
  emptyWorldBookForm,
  formToPayload,
  validateWorldBook,
  WorldBookForm,
  WorldBookFormView
} from "../_components/WorldBookForm";

export default function NewWorldBookPage() {
  const router = useRouter();
  const [form, setForm] = useState<WorldBookForm>(emptyWorldBookForm);
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [hasTriedSubmit, setHasTriedSubmit] = useState(false);
  const validationError = validateWorldBook(form);

  const updateField = (field: keyof WorldBookForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    setHasUnsavedChanges(true);
    setError("");
  };

  const guardLeaveToList = (event: MouseEvent<HTMLAnchorElement>) => {
    if (hasUnsavedChanges && !window.confirm("当前页面有未保存内容，确认离开吗？")) {
      event.preventDefault();
    }
  };

  const saveWorldBook = async (event: FormEvent) => {
    event.preventDefault();
    setHasTriedSubmit(true);
    setError("");

    if (validationError) {
      return;
    }

    setIsSaving(true);
    try {
      const saved = await createWorldBook(formToPayload(form));
      setHasUnsavedChanges(false);
      router.push(`/world-books/${saved.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "世界观创建失败");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">新建世界观</h1>
          <p className="page-description">创建可在多个短剧项目中复用的故事世界设定。项目加载后会保存独立快照。</p>
        </div>
        <Button className="button secondary" asChild>
          <Link href="/world-books" onClick={guardLeaveToList}>返回列表</Link>
        </Button>
      </header>

      <form className="panel stack form-page" onSubmit={saveWorldBook}>
        <div className="section-heading">
          <h2>世界观设定</h2>
          {hasUnsavedChanges ? <span className="warning-text">有未保存内容</span> : null}
        </div>

        <WorldBookFormView form={form} onChange={updateField} hideStatusField />

        {hasTriedSubmit && validationError ? <div className="error">{validationError}</div> : null}
        {error ? <div className="error">{error}</div> : null}

        <div className="actions action-wrap">
          <Button className="button secondary" asChild>
            <Link href="/world-books" onClick={guardLeaveToList}>取消</Link>
          </Button>
          <Button className="button" type="submit" disabled={isSaving}>
            {isSaving ? "保存中..." : "保存世界观"}
          </Button>
        </div>
      </form>
    </div>
  );
}
