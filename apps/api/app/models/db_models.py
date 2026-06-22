"""数据库模型模块，定义项目、资产库、生成内容和配置相关数据表。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ModelApiConfig(Base):
    """模型 API 配置表，保存文本和图片模型的调用参数。"""
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
    """模型配置测试日志表，保留每次连通性测试结果。"""
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
    """短剧项目表，保存项目基础设定和时长约束。"""
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
    """角色卡资产表，保存可跨项目复用的人物设定和视觉素材。"""
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
    """项目角色快照表，保存角色卡加载到项目后的独立副本。"""
    __tablename__ = "project_character_snapshots"
    __table_args__ = (
        CheckConstraint("gender in ('男', '女')", name="ck_project_character_snapshots_gender"),
        UniqueConstraint("project_id", "source_character_card_id", name="uq_project_character_snapshots_project_source"),
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
    """世界观资产表，保存可跨项目复用的世界设定。"""
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
    """世界观条目表，保存关键词触发的世界观局部信息。"""
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
    """项目世界观快照表，保存世界观加载到项目后的独立副本。"""
    __tablename__ = "project_world_snapshots"
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_project_world_snapshots_project"),
    )

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


class ProjectStoryOutline(Base):
    """项目故事大纲表，保存整体故事脉络和关键结构。"""
    __tablename__ = "project_story_outlines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, unique=True, index=True)
    logline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    story_background: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    core_conflict: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    main_goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    story_start: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plot_structure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reversals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emotion_curve: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    foreshadowing: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    character_arcs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ending_direction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pacing_advice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    capacity_advice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ReferenceStoryStructureDraft(Base):
    """参考故事结构草稿表，保存从样本文本抽取的可复用结构。"""
    __tablename__ = "project_story_structure_drafts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(24), nullable=False)
    source_filename: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    source_text_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    story_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    goal_model: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inciting_event_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conflict_model: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stage_structure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reversal_mechanism: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emotion_curve: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    foreshadowing_pattern: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ending_pattern: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    adaptation_advice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    de_specificity_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    validation_status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", index=True)
    validation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProjectEpisodeOutline(Base):
    """项目分集大纲表，保存单集剧情骨架。"""
    __tablename__ = "project_episode_outlines"
    __table_args__ = (
        UniqueConstraint("project_id", "episode_no", name="uq_project_episode_outlines_project_episode"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    episode_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    synopsis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hook: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conflict: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reversal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cliffhanger: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProjectEpisodeContent(Base):
    """项目单集正文表，保存单集详细故事内容。"""
    __tablename__ = "project_episode_contents"
    __table_args__ = (
        UniqueConstraint("project_id", "episode_no", name="uq_project_episode_contents_project_episode"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    episode_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    detailed_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chapter_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hook: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_beats: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    previous_context_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quality_check_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EpisodeContentGenerationVersion(Base):
    """单集正文 AI 生成候选版本，采用前不覆盖正式正文。"""
    __tablename__ = "episode_content_generation_versions"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "episode_no",
            "client_request_id",
            name="uq_episode_content_generations_request",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    episode_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    instruction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    output_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="candidate", index=True)
    client_request_id: Mapped[str] = mapped_column(String(80), nullable=False)
    model_config_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    elapsed_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    adopted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ProjectEpisodeScript(Base):
    """项目单集结构化剧本聚合根。"""
    __tablename__ = "project_episode_scripts"
    __table_args__ = (
        UniqueConstraint("project_id", "episode_no", name="uq_project_episode_scripts_project_episode"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    episode_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    scene_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dialogue: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voiceover: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_content_version: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    auto_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    manual_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    effective_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", index=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProjectScriptScene(Base):
    """结构化剧本场次，顺序由服务端统一规范化。"""
    __tablename__ = "project_script_scenes"
    __table_args__ = (UniqueConstraint("script_id", "sort_order", name="uq_project_script_scenes_order"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    script_id: Mapped[str] = mapped_column(String(64), ForeignKey("project_episode_scripts.id"), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    time_of_day: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    interior_exterior: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    character_snapshot_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    auto_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    manual_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    effective_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    story_purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProjectScriptBlock(Base):
    """结构化剧本内容块，按真实叙事顺序保存。"""
    __tablename__ = "project_script_blocks"
    __table_args__ = (UniqueConstraint("scene_id", "sort_order", name="uq_project_script_blocks_order"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scene_id: Mapped[str] = mapped_column(String(64), ForeignKey("project_script_scenes.id"), nullable=False, index=True)
    block_type: Mapped[str] = mapped_column(String(24), nullable=False)
    character_snapshot_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("project_character_snapshots.id"), nullable=True, index=True
    )
    temporary_speaker_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emotion: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    performance_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProjectEpisodeScriptVersion(Base):
    """不可变的结构化剧本正式版本快照。"""
    __tablename__ = "project_episode_script_versions"
    __table_args__ = (UniqueConstraint("script_id", "version", name="uq_project_episode_script_versions_number"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    script_id: Mapped[str] = mapped_column(String(64), ForeignKey("project_episode_scripts.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    source_content_version: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    change_source: Mapped[str] = mapped_column(String(32), nullable=False)
    generation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProjectScriptGeneration(Base):
    """整集、场次或连续内容块改写生成的候选记录。"""
    __tablename__ = "project_script_generations"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "episode_no", "generation_scope", "client_request_id",
            name="uq_project_script_generations_request",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    episode_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    generation_scope: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    target_scene_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_block_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    rewrite_preset: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    instruction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    base_script_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    base_script_revision: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    output_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="candidate", index=True)
    client_request_id: Mapped[str] = mapped_column(String(80), nullable=False)
    model_config_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    elapsed_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    adopted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProjectScriptCheckRun(Base):
    """结构化剧本检查结果，绑定具体正式版本与修订号。"""
    __tablename__ = "project_script_check_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    script_id: Mapped[str] = mapped_column(String(64), ForeignKey("project_episode_scripts.id"), nullable=False, index=True)
    script_version: Mapped[int] = mapped_column(Integer, nullable=False)
    script_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(24), nullable=False)
    semantic_check_status: Mapped[str] = mapped_column(String(24), nullable=False)
    issues: Mapped[str] = mapped_column(Text, nullable=False)
    model_config_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProjectStoryboardShot(Base):
    """项目分镜表，保存单集镜头级制作信息。"""
    __tablename__ = "project_storyboard_shots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    episode_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    shot_no: Mapped[int] = mapped_column(Integer, nullable=False)
    scene: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    visual_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    camera: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dialogue_or_voiceover: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProjectCopywriting(Base):
    """项目发布文案表，保存字幕、标题、简介和发布文案。"""
    __tablename__ = "project_copywriting"
    __table_args__ = (
        UniqueConstraint("project_id", "episode_no", name="uq_project_copywriting_project_episode"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    episode_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    subtitles: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    platform_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    platform_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    publish_copy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
