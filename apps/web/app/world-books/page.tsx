"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { SimpleSelect } from "@/components/ui/simple-select";
import { Skeleton } from "@/components/ui/skeleton";
import { activateWorldBook, archiveWorldBook, listWorldBooks, WorldBook } from "@/lib/api";
import { worldBookGenres, worldBookStatuses, worldBookStatusLabel } from "./_components/WorldBookForm";

export default function WorldBooksPage() {
  const [worldBooks, setWorldBooks] = useState<WorldBook[]>([]);
  const [search, setSearch] = useState("");
  const [genreFilter, setGenreFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [archivingWorldBookId, setArchivingWorldBookId] = useState("");
  const [activatingWorldBookId, setActivatingWorldBookId] = useState("");
  const [worldBookPendingArchive, setWorldBookPendingArchive] = useState<WorldBook | null>(null);
  const genreFilterOptions = Array.from(new Set([...worldBookGenres, ...worldBooks.map((book) => book.genre)]));

  useEffect(() => {
    void refreshWorldBooks();
  }, []);

  const refreshWorldBooks = async () => {
    setIsLoading(true);
    setError("");
    setStatusMessage("");
    try {
      const items = await listWorldBooks({
        search: search.trim() || undefined,
        genre: genreFilter || undefined,
        status: statusFilter || undefined
      });
      setWorldBooks(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "世界观列表加载失败");
    } finally {
      setIsLoading(false);
    }
  };

  const archiveBook = (book: WorldBook) => {
    setWorldBookPendingArchive(book);
  };

  const confirmArchiveBook = async () => {
    if (!worldBookPendingArchive) return;
    setArchivingWorldBookId(worldBookPendingArchive.id);
    setError("");
    setStatusMessage("");
    try {
      const archived = await archiveWorldBook(worldBookPendingArchive.id);
      setWorldBooks((current) => current.map((item) => (item.id === archived.id ? archived : item)));
      setStatusMessage("世界观已归档。");
      setWorldBookPendingArchive(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "世界观归档失败");
    } finally {
      setArchivingWorldBookId("");
    }
  };

  const activateBook = async (book: WorldBook) => {
    setActivatingWorldBookId(book.id);
    setError("");
    setStatusMessage("");
    try {
      const activated = await activateWorldBook(book.id);
      setWorldBooks((current) => current.map((item) => (item.id === activated.id ? activated : item)));
      setStatusMessage("世界观已设为可加载。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "世界观启用失败");
    } finally {
      setActivatingWorldBookId("");
    }
  };

  return (
    <div className="stack">
      <ConfirmDialog
        destructive
        open={Boolean(worldBookPendingArchive)}
        title="归档世界观？"
        description="归档后，该世界观不再作为新项目可选项。已有项目快照不会被删除。"
        confirmLabel="归档"
        onOpenChange={(open) => {
          if (!open) setWorldBookPendingArchive(null);
        }}
        onConfirm={() => void confirmArchiveBook()}
      />
      <header className="page-header">
        <div>
          <h1 className="page-title">世界观库</h1>
          <p className="page-description">
            管理可复用故事世界设定。世界观加载到项目后会生成独立快照，项目内修改不会影响资产库原始内容。
          </p>
        </div>
        <Button asChild>
          <Link href="/world-books/new">新建世界观</Link>
        </Button>
      </header>

      <section className="panel stack">
        <div className="section-heading">
          <h2>世界观列表</h2>
          <span className="hint">{isLoading ? "加载中..." : `${worldBooks.length} 个世界观`}</span>
        </div>

        <div className="filter-bar filter-bar-compact">
          <Field label="搜索世界观">
            <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="输入名称、题材或摘要" />
          </Field>
          <Field label="题材类型">
            <SimpleSelect
              value={genreFilter}
              onValueChange={setGenreFilter}
              options={[{ label: "全部题材", value: "" }, ...genreFilterOptions.map((genre) => ({ label: genre, value: genre }))]}
            />
          </Field>
          <Field label="状态">
            <SimpleSelect value={statusFilter} onValueChange={setStatusFilter} options={worldBookStatuses} />
          </Field>
          <div className="filter-actions">
            <Button variant="secondary" type="button" onClick={refreshWorldBooks} disabled={isLoading}>
              筛选
            </Button>
          </div>
        </div>

        {error ? <div className="error">{error}</div> : null}
        {statusMessage ? <div className="success">{statusMessage}</div> : null}

        <div className="asset-list asset-list-wide">
          {isLoading ? <AssetListSkeleton /> : null}

          {worldBooks.length === 0 && !isLoading ? (
            <div className="empty-state">
              <p>还没有世界观。</p>
              <Button asChild>
                <Link href="/world-books/new">新建第一个世界观</Link>
              </Button>
            </div>
          ) : null}

          {worldBooks.map((book) => (
            <article className="asset-card" key={book.id}>
              <Link className="asset-card-main" href={`/world-books/${book.id}`}>
                <div className="asset-card-title">
                  <strong>{book.name}</strong>
                  <Badge className={`status-badge status-${book.status}`}>{worldBookStatusLabel(book.status)}</Badge>
                </div>
                <div className="hint">
                  {book.genre} · {book.active_entry_count}/{book.entry_count} 个可用条目 · v{book.version} ·{" "}
                  {new Date(book.updated_at).toLocaleString()}
                </div>
                <p>{book.summary || book.era_background || "未填写摘要或时代背景"}</p>
                <p className="hint">核心规则：{book.world_rules}</p>
                <p className="hint">{book.tone_style || "未设置整体风格"}</p>
              </Link>
              <div className="asset-card-actions">
                <Button variant="secondary" asChild>
                  <Link href={`/world-books/${book.id}`}>查看详情</Link>
                </Button>
                {book.status !== "active" && (
                  <Button

                    type="button"
                    onClick={() => void activateBook(book)}
                    disabled={activatingWorldBookId === book.id}
                  >
                    {activatingWorldBookId === book.id ? "启用中..." : "设为可加载"}
                  </Button>
                )}
                <Button
                  variant="destructive"
                  type="button"
                  onClick={() => archiveBook(book)}
                  disabled={book.status === "archived" || archivingWorldBookId === book.id}
                >
                  {archivingWorldBookId === book.id ? "归档中..." : "归档"}
                </Button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function AssetListSkeleton() {
  return (
    <>
      {Array.from({ length: 3 }, (_, index) => (
        <div className="asset-card" key={index} aria-label="世界观加载中">
          <div className="asset-card-main">
            <Skeleton className="h-5 w-44" />
            <Skeleton className="h-4 w-80 max-w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
          <div className="asset-card-actions">
            <Skeleton className="h-9 w-20" />
            <Skeleton className="h-9 w-20" />
          </div>
        </div>
      ))}
    </>
  );
}
