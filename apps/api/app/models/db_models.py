from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ModelApiConfig(Base):
    __tablename__ = "model_api_configs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    config_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    provider_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="custom")
    provider_preset: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False)
    api_base_url: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_secret: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String(160), nullable=False)
    image_size: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    endpoint_path: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    # 图片模型是否支持参考图输入，决定角色三视图能否真正携带上传图片参与生成。
    supports_reference_image: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_test_status: Mapped[str] = mapped_column(String(24), nullable=False, default="untested")
    last_tested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # 模型配置采用软删除，保留测试日志用于后续排查接口失败原因。
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ModelApiTestLog(Base):
    __tablename__ = "model_api_test_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    config_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("model_api_configs.id"), nullable=False, index=True
    )
    config_type: Mapped[str] = mapped_column(String(16), nullable=False)
    request_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    response_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    idea: Mapped[str] = mapped_column(Text, nullable=False)
    target_platform: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    genre: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    episode_count: Mapped[int] = mapped_column(Integer, nullable=False)
    episode_duration: Mapped[float] = mapped_column(Float, nullable=False)
    total_duration: Mapped[float] = mapped_column(Float, nullable=False)
    target_audience: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    style: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CharacterCard(Base):
    __tablename__ = "character_cards"
    __table_args__ = (
        CheckConstraint("gender in ('男', '女')", name="ck_character_cards_gender"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    # 性别是生成故事上下文、称谓和人物视觉方向的基础约束，只允许男或女。
    gender: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    role_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    identity: Mapped[str] = mapped_column(String(200), nullable=False)
    background: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    personality: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    motivation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    secret: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conflict_points: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relationship_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    speech_style: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    catchphrases: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emotional_arc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    story_function: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    visual_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_local_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    turnaround_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    turnaround_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    turnaround_local_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    turnaround_generation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 三视图先生成候选图，只有用户确认后才作为后续视频一致性的参考素材。
    turnaround_status: Mapped[str] = mapped_column(String(24), nullable=False, default="none")
    turnaround_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    turnaround_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # 版本号用于判断已加载到项目的角色快照是否落后于原始角色卡。
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # archived 角色卡不再作为新项目加载候选，但历史项目仍需保留来源追踪。
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProjectCharacterSnapshot(Base):
    __tablename__ = "project_character_snapshots"
    __table_args__ = (
        CheckConstraint("gender in ('男', '女')", name="ck_project_character_snapshots_gender"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    source_character_card_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("character_cards.id"), nullable=False, index=True
    )
    source_version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    # 快照保留加载时的性别，后续项目内修改不会影响原始角色卡。
    gender: Mapped[str] = mapped_column(String(4), nullable=False)
    role_type: Mapped[str] = mapped_column(String(40), nullable=False)
    # 快照保存加载时的完整角色内容，项目内编辑不会回写原始角色卡。
    snapshot_content: Mapped[str] = mapped_column(Text, nullable=False)
    visual_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_local_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    loaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorldBook(Base):
    __tablename__ = "world_books"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    genre: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    era_background: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    world_rules: Mapped[str] = mapped_column(Text, nullable=False)
    organizations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    locations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    social_structure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    taboo_or_constraints: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tone_style: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorldEntry(Base):
    __tablename__ = "world_entries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    world_book_id: Mapped[str] = mapped_column(String(64), ForeignKey("world_books.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entry_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    applicable_scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProjectWorldSnapshot(Base):
    __tablename__ = "project_world_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    source_world_book_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("world_books.id"), nullable=False, index=True
    )
    source_version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    genre: Mapped[str] = mapped_column(String(120), nullable=False)
    snapshot_content: Mapped[str] = mapped_column(Text, nullable=False)
    entry_snapshot_content: Mapped[str] = mapped_column(Text, nullable=False)
    loaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
