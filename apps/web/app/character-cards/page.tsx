"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SimpleSelect } from "@/components/ui/simple-select";
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

  const archiveCard = async (card: CharacterCard) => {
    if (!window.confirm("归档后，该角色卡不再作为新项目可选项。确认归档？")) {
      return;
    }

    setArchivingCardId(card.id);
    setError("");
    setStatusMessage("");
    try {
      const archived = await archiveCharacterCard(card.id);
      setCards((current) => current.map((item) => (item.id === archived.id ? archived : item)));
      setStatusMessage("角色卡已归档。");
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
          <div className="field">
            <label>搜索角色名</label>
            <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="输入角色名或身份摘要" />
          </div>
          <div className="field">
            <label>性别</label>
            <SimpleSelect
              value={genderFilter}
              onValueChange={(value) => setGenderFilter(value as "" | CharacterGender)}
              options={[{ label: "全部性别", value: "" }, ...genderOptions.map((gender) => ({ label: gender, value: gender }))]}
            />
          </div>
          <div className="field">
            <label>人物原型</label>
            <SimpleSelect
              value={roleFilter}
              onValueChange={setRoleFilter}
              options={[{ label: "全部原型", value: "" }, ...roleFilterOptions.map((role) => ({ label: role, value: role }))]}
            />
          </div>
          <div className="field">
            <label>状态</label>
            <SimpleSelect value={statusFilter} onValueChange={setStatusFilter} options={statuses} />
          </div>
          <div className="filter-actions">
            <Button variant="secondary" type="button" onClick={refreshCards} disabled={isLoading}>
              筛选
            </Button>
          </div>
        </div>

        {error ? <div className="error">{error}</div> : null}
        {statusMessage ? <div className="success">{statusMessage}</div> : null}

        <div className="asset-list asset-list-wide">
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
