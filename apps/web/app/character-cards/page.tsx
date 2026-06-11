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
import { activateCharacterCard, archiveCharacterCard, CharacterCard, CharacterGender, listCharacterCards } from "@/lib/api";
import { genderOptions, roleTypes, statuses, statusLabel } from "./_components/CharacterCardForm";

export default function CharacterCardsPage() {
  const [cards, setCards] = useState<CharacterCard[]>([]);
  const [search, setSearch] = useState("");
  const [genderFilter, setGenderFilter] = useState<"" | CharacterGender>("");
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [archivingCardId, setArchivingCardId] = useState("");
  const [activatingCardId, setActivatingCardId] = useState("");
  const [cardPendingArchive, setCardPendingArchive] = useState<CharacterCard | null>(null);
  // 列表筛选保留旧数据中的原始类型值，避免字段边界调整后旧角色卡无法按原值筛选。
  const roleFilterOptions = Array.from(new Set([...roleTypes, ...cards.map((card) => card.role_type)]));

  useEffect(() => {
    void refreshCards();
  }, []);

  const refreshCards = async () => {
    setIsLoading(true);
    setError("");
    setStatusMessage("");
    try {
      const cardList = await listCharacterCards({
        search: search.trim() || undefined,
        gender: genderFilter || undefined,
        role_type: roleFilter || undefined,
        status: statusFilter || undefined
      });
      setCards(cardList);
    } catch (err) {
      setError(err instanceof Error ? err.message : "角色卡列表加载失败");
    } finally {
      setIsLoading(false);
    }
  };

  const archiveCard = (card: CharacterCard) => {
    setCardPendingArchive(card);
  };

  const confirmArchiveCard = async () => {
    if (!cardPendingArchive) return;
    setArchivingCardId(cardPendingArchive.id);
    setError("");
    setStatusMessage("");
    try {
      const archived = await archiveCharacterCard(cardPendingArchive.id);
      setCards((current) => current.map((item) => (item.id === archived.id ? archived : item)));
      setStatusMessage("角色卡已归档。");
      setCardPendingArchive(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "角色卡归档失败");
    } finally {
      setArchivingCardId("");
    }
  };

  const activateCard = async (card: CharacterCard) => {
    setActivatingCardId(card.id);
    setError("");
    setStatusMessage("");
    try {
      const activated = await activateCharacterCard(card.id);
      setCards((current) => current.map((item) => (item.id === activated.id ? activated : item)));
      setStatusMessage("角色卡已设为可加载。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "角色卡启用失败");
    } finally {
      setActivatingCardId("");
    }
  };

  return (
    <div className="stack">
      <ConfirmDialog
        destructive
        open={Boolean(cardPendingArchive)}
        title="归档角色卡？"
        description="归档后，该角色卡不再作为新项目可选项。已有项目快照不会被删除。"
        confirmLabel="归档"
        onOpenChange={(open) => {
          if (!open) setCardPendingArchive(null);
        }}
        onConfirm={() => void confirmArchiveCard()}
      />
      <header className="page-header">
        <div>
          <h1 className="page-title">角色卡库</h1>
          <p className="page-description">
            管理可复用人物资产。角色卡只保存跨项目稳定的人设、口吻和视觉素材，具体剧情在项目内塑造。
          </p>
        </div>
        <Button asChild>
          <Link href="/character-cards/new">新建角色卡</Link>
        </Button>
      </header>

      <section className="panel stack">
        <div className="section-heading">
          <h2>角色列表</h2>
          <span className="hint">{isLoading ? "加载中..." : `${cards.length} 个角色`}</span>
        </div>

        <div className="filter-bar">
          <Field label="搜索角色名">
            <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="输入角色名或身份摘要" />
          </Field>
          <Field label="性别">
            <SimpleSelect
              value={genderFilter}
              onValueChange={(value) => setGenderFilter(value as "" | CharacterGender)}
              options={[{ label: "全部性别", value: "" }, ...genderOptions.map((gender) => ({ label: gender, value: gender }))]}
            />
          </Field>
          <Field label="人物原型">
            <SimpleSelect
              value={roleFilter}
              onValueChange={setRoleFilter}
              options={[{ label: "全部原型", value: "" }, ...roleFilterOptions.map((role) => ({ label: role, value: role }))]}
            />
          </Field>
          <Field label="状态">
            <SimpleSelect value={statusFilter} onValueChange={setStatusFilter} options={statuses} />
          </Field>
          <div className="filter-actions">
            <Button variant="secondary" type="button" onClick={refreshCards} disabled={isLoading}>
              筛选
            </Button>
          </div>
        </div>

        {error ? <div className="error">{error}</div> : null}
        {statusMessage ? <div className="success">{statusMessage}</div> : null}

        <div className="asset-list asset-list-wide">
          {isLoading ? <AssetListSkeleton /> : null}

          {cards.length === 0 && !isLoading ? (
            <div className="empty-state">
              <p>还没有角色卡。</p>
              <Button asChild>
                <Link href="/character-cards/new">新建第一个角色卡</Link>
              </Button>
            </div>
          ) : null}

          {cards.map((card) => (
            <article className="asset-card" key={card.id}>
              <Link className="asset-card-main" href={`/character-cards/${card.id}`}>
                <div className="asset-card-title">
                  <strong>{card.name}</strong>
                  <Badge className={`status-badge status-${card.status}`}>{statusLabel(card.status)}</Badge>
                </div>
                <div className="hint">
                  {card.gender} · {card.role_type} · v{card.version} · {new Date(card.updated_at).toLocaleString()}
                </div>
                <p>{card.identity}</p>
                <p className="hint">核心欲望 / 人物执念：{card.goal}</p>
                <p className="hint">{card.image_keywords || "未设置形象关键词"}</p>
              </Link>
              <div className="asset-card-actions">
                <Button variant="secondary" asChild>
                  <Link href={`/character-cards/${card.id}`}>查看详情</Link>
                </Button>
                {card.status !== "active" && (
                  <Button

                    type="button"
                    onClick={() => void activateCard(card)}
                    disabled={activatingCardId === card.id}
                  >
                    {activatingCardId === card.id ? "启用中..." : "设为可加载"}
                  </Button>
                )}
                <Button
                  variant="destructive"
                  type="button"
                  onClick={() => archiveCard(card)}
                  disabled={card.status === "archived" || archivingCardId === card.id}
                >
                  {archivingCardId === card.id ? "归档中..." : "归档"}
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
        <div className="asset-card" key={index} aria-label="角色卡加载中">
          <div className="asset-card-main">
            <Skeleton className="h-5 w-44" />
            <Skeleton className="h-4 w-72 max-w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
          <div className="asset-card-actions">
            <Skeleton className="h-9 w-20" />
            <Skeleton className="h-9 w-24" />
          </div>
        </div>
      ))}
    </>
  );
}
