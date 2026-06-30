"""接口 Schema 模块，定义 FastAPI 请求体与响应体的数据边界。"""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


ConfigType = Literal["text", "image", "video"]
ProviderMode = Literal["preset", "custom"]
CharacterGender = Literal["男", "女"]
CharacterCardStatus = Literal["draft", "active", "archived"]
WorldBookStatus = Literal["draft", "active", "archived"]
WorldEntryStatus = Literal["active", "disabled"]
WorldEntryType = Literal["世界规则", "地点", "组织", "阶层关系", "历史事件", "特殊物品", "禁忌或限制", "风格约束", "其他"]
ProjectArtifactStatus = Literal["draft", "confirmed", "needs_review"]
ReferenceStorySourceType = Literal["pasted", "uploaded"]
ReferenceStoryDraftStatus = Literal["draft", "applied", "discarded"]
ReferenceStoryValidationStatus = Literal["pending", "passed", "failed"]
StoryOutlineWriteMode = Literal["preview", "apply"]
ReferenceStoryApplyMode = Literal["fill_empty", "overwrite"]
StoryOutlineAssistAction = Literal["start", "reply"]
StoryOutlineAssistMessageRole = Literal["user", "assistant"]
EpisodeContentGenerationStatus = Literal["candidate", "adopted", "discarded"]
EpisodeContentGenerationType = Literal["create", "continue", "polish"]
ScriptStatus = Literal["draft", "pending_review", "confirmed", "needs_review"]
ScriptBlockType = Literal["action", "dialogue", "voiceover", "transition"]
ScriptTimeOfDay = Literal["morning", "day", "dusk", "night", "other"]
ScriptInteriorExterior = Literal["interior", "exterior", "mixed"]
ScriptGenerationScope = Literal["episode", "scene", "blocks"]
ScriptGenerationStatus = Literal["candidate", "adopted", "discarded"]
StoryboardStatus = Literal["draft", "pending_review", "confirmed", "needs_review"]
StoryboardSourceStatus = Literal["valid", "changed", "scene_deleted", "unassigned"]
ShotVideoGenerationStatus = Literal["queued", "running", "succeeded", "failed", "canceled"]
ScriptRewritePreset = Literal[
    "more_satisfying", "more_tragic", "more_suspenseful", "more_colloquial",
    "short_video_pacing", "compress_duration", "stronger_cliffhanger",
]


class ModelApiConfigCreate(BaseModel):
    """ModelApiConfigCreate 创建请求体，用于约束接口数据结构。"""
    config_type: ConfigType
    provider_mode: ProviderMode = "custom"
    provider_preset: Optional[str] = None
    provider_name: Optional[str] = None
    api_base_url: Optional[str] = None
    api_key: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    image_size: Optional[str] = None
    endpoint_path: Optional[str] = None
    supports_reference_image: bool = False
    remark: Optional[str] = None
    enabled: bool = True

    @field_validator(
        "provider_preset",
        "provider_name",
        "api_base_url",
        "api_key",
        "model_name",
        "image_size",
        "endpoint_path",
        "remark",
        mode="before",
    )
    @classmethod
    def normalize_config_text(cls, value: Optional[str]) -> Optional[str]:
        """清理模型配置文本字段，空字符串统一转为空值以便后续供应商规则校验。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ModelApiConfigUpdate(BaseModel):
    """ModelApiConfigUpdate 更新请求体，用于约束接口数据结构。"""
    provider_mode: ProviderMode = "custom"
    provider_preset: Optional[str] = None
    provider_name: Optional[str] = None
    api_base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: str = Field(min_length=1)
    image_size: Optional[str] = None
    endpoint_path: Optional[str] = None
    supports_reference_image: bool = False
    remark: Optional[str] = None
    enabled: Optional[bool] = None

    @field_validator(
        "provider_preset",
        "provider_name",
        "api_base_url",
        "api_key",
        "model_name",
        "image_size",
        "endpoint_path",
        "remark",
        mode="before",
    )
    @classmethod
    def normalize_config_text(cls, value: Optional[str]) -> Optional[str]:
        """清理模型配置更新字段，避免空白字符串覆盖有效配置。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ModelApiConfigResponse(BaseModel):
    """ModelApiConfigResponse 响应体，用于约束接口数据结构。"""
    id: str
    config_type: ConfigType
    provider_mode: ProviderMode
    provider_preset: Optional[str]
    provider_name: str
    api_base_url: str
    api_key_masked: str
    model_name: str
    image_size: Optional[str]
    endpoint_path: Optional[str]
    supports_reference_image: bool
    remark: Optional[str]
    enabled: bool
    last_test_status: str
    last_tested_at: Optional[str]
    last_test_error: Optional[str]
    created_at: str
    updated_at: str


class ModelApiTestResponse(BaseModel):
    """ModelApiTestResponse 响应体，用于约束接口数据结构。"""
    success: bool
    status: str
    message: str
    latency_ms: Optional[int] = None
    tested_at: str


class UserSkillUpdate(BaseModel):
    """UserSkillUpdate 更新请求体，用于切换用户侧业务 Skill。"""
    enabled: bool


class UserSkillResponse(BaseModel):
    """UserSkillResponse 响应体，用于展示用户侧业务 Skill。"""
    name: str
    description: str
    source_dir: str
    enabled: bool
    updated_at: Optional[str] = None


class ProjectCreate(BaseModel):
    """ProjectCreate 创建请求体，用于约束接口数据结构。"""
    title: Optional[str] = None
    idea: str
    target_platform: Optional[str] = "抖音"
    genre: Optional[str] = None
    episode_count: int = 20
    episode_duration: float = 1
    target_audience: Optional[str] = None
    style: Optional[str] = None
    remark: Optional[str] = None

    @field_validator("idea", mode="before")
    @classmethod
    def validate_idea(cls, value: Optional[str]) -> str:
        """校验项目创意不能为空，这是后续 AI 生成流程的最小输入。"""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("请先输入短剧创意描述")
        return value.strip()

    @field_validator("episode_count")
    @classmethod
    def validate_episode_count(cls, value: int) -> int:
        """校验项目集数必须为正整数，防止生成无效分集结构。"""
        if value <= 0:
            raise ValueError("集数必须是大于 0 的整数")
        return value

    @field_validator("episode_duration")
    @classmethod
    def validate_episode_duration(cls, value: float) -> float:
        """校验单集时长不能超过 2 分钟，和一期产品时长规则保持一致。"""
        if value <= 0:
            raise ValueError("单集时长必须大于 0 分钟")
        if value > 2:
            raise ValueError("单集时长不能超过 2 分钟")
        return value


class ProjectUpdate(ProjectCreate):
    """ProjectUpdate 更新请求体，用于约束接口数据结构。"""
    pass


class ProjectResponse(BaseModel):
    """ProjectResponse 响应体，用于约束接口数据结构。"""
    id: str
    title: str
    idea: str
    target_platform: Optional[str]
    genre: Optional[str]
    episode_count: int
    episode_duration: float
    total_duration: float
    target_audience: Optional[str]
    style: Optional[str]
    remark: Optional[str]
    status: str
    created_at: str
    updated_at: str


class CharacterCardBase(BaseModel):
    """CharacterCardBase 数据结构，定义接口层使用的数据字段。"""
    name: str = Field(min_length=1, max_length=80)
    gender: CharacterGender
    role_type: str = Field(min_length=1, max_length=40)
    identity: str = Field(min_length=1, max_length=200)
    background: Optional[str] = None
    personality: Optional[str] = None
    goal: str = Field(min_length=1)
    motivation: Optional[str] = None
    secret: Optional[str] = None
    conflict_points: Optional[str] = None
    relationship_notes: Optional[str] = None
    speech_style: Optional[str] = None
    catchphrases: Optional[str] = None
    emotional_arc: Optional[str] = None
    story_function: Optional[str] = None
    visual_description: Optional[str] = None
    image_keywords: Optional[str] = None
    reference_image_url: Optional[str] = None
    reference_local_path: Optional[str] = None
    turnaround_prompt: Optional[str] = None
    status: CharacterCardStatus = "draft"

    @field_validator(
        "name",
        "role_type",
        "identity",
        "background",
        "personality",
        "goal",
        "motivation",
        "secret",
        "conflict_points",
        "relationship_notes",
        "speech_style",
        "catchphrases",
        "emotional_arc",
        "story_function",
        "visual_description",
        "image_keywords",
        "reference_image_url",
        "reference_local_path",
        "turnaround_prompt",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理角色卡文本字段，隐藏的历史剧情字段也保留兼容写入能力。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("gender", mode="before")
    @classmethod
    def validate_gender(cls, value: Optional[str]) -> str:
        """校验角色性别只能是男或女，用于生成称谓和视觉方向。"""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("性别不能为空")
        gender = value.strip()
        if gender not in {"男", "女"}:
            raise ValueError("性别只能选择男或女")
        return gender


class CharacterCardCreate(CharacterCardBase):
    """CharacterCardCreate 创建请求体，用于约束接口数据结构。"""
    pass


class CharacterCardUpdate(CharacterCardBase):
    """CharacterCardUpdate 更新请求体，用于约束接口数据结构。"""
    pass


class CharacterCardResponse(CharacterCardBase):
    """CharacterCardResponse 响应体，用于约束接口数据结构。"""
    id: str
    version: int
    turnaround_image_url: Optional[str] = None
    turnaround_local_path: Optional[str] = None
    turnaround_generation_prompt: Optional[str] = None
    turnaround_status: str = "none"
    turnaround_version: int = 0
    turnaround_confirmed_at: Optional[str] = None
    created_at: str
    updated_at: str


class CharacterReferenceImageUpload(BaseModel):
    """CharacterReferenceImageUpload 数据结构，定义接口层使用的数据字段。"""
    filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    data_url: str = Field(min_length=1)


class CharacterImageAssetResponse(BaseModel):
    """CharacterImageAssetResponse 响应体，用于约束接口数据结构。"""
    character_card_id: str
    image_url: str
    local_path: str
    updated_at: str


class CharacterTurnaroundGenerate(BaseModel):
    """CharacterTurnaroundGenerate 数据结构，定义接口层使用的数据字段。"""
    prompt: Optional[str] = None


class CharacterTurnaroundResponse(BaseModel):
    """CharacterTurnaroundResponse 响应体，用于约束接口数据结构。"""
    character_card_id: str
    image_url: Optional[str] = None
    local_path: Optional[str] = None
    generation_prompt: Optional[str] = None
    status: str
    version: int
    confirmed_at: Optional[str] = None
    updated_at: str


class ProjectCharacterSnapshotCreate(BaseModel):
    """ProjectCharacterSnapshotCreate 创建请求体，用于约束接口数据结构。"""
    source_character_card_id: str = Field(min_length=1)
    load_mode: Literal["new", "replace"] = "new"
    replace_snapshot_id: Optional[str] = None


class ProjectCharacterSnapshotUpdate(BaseModel):
    """ProjectCharacterSnapshotUpdate 更新请求体，用于约束接口数据结构。"""
    name: str = Field(min_length=1, max_length=80)
    gender: CharacterGender
    role_type: str = Field(min_length=1, max_length=40)
    snapshot_content: str = Field(min_length=1)
    visual_description: Optional[str] = None
    reference_image_url: Optional[str] = None
    reference_local_path: Optional[str] = None

    @field_validator(
        "name",
        "role_type",
        "snapshot_content",
        "visual_description",
        "reference_image_url",
        "reference_local_path",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理项目角色快照文本字段，只影响当前项目副本。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("gender", mode="before")
    @classmethod
    def validate_gender(cls, value: Optional[str]) -> str:
        """校验项目角色快照性别只能是男或女，保持和角色卡资产一致。"""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("性别不能为空")
        gender = value.strip()
        if gender not in {"男", "女"}:
            raise ValueError("性别只能选择男或女")
        return gender


class ProjectCharacterSnapshotResponse(BaseModel):
    """ProjectCharacterSnapshotResponse 响应体，用于约束接口数据结构。"""
    id: str
    project_id: str
    source_character_card_id: str
    source_version: int
    name: str
    gender: CharacterGender
    role_type: str
    snapshot_content: str
    visual_description: Optional[str]
    reference_image_url: Optional[str]
    reference_local_path: Optional[str]
    loaded_at: str
    updated_at: str


class WorldBookBase(BaseModel):
    """WorldBookBase 数据结构，定义接口层使用的数据字段。"""
    name: str = Field(min_length=1, max_length=120)
    genre: str = Field(min_length=1, max_length=120)
    era_background: Optional[str] = None
    world_rules: str = Field(min_length=1)
    organizations: Optional[str] = None
    locations: Optional[str] = None
    social_structure: Optional[str] = None
    taboo_or_constraints: Optional[str] = None
    tone_style: Optional[str] = None
    summary: Optional[str] = None
    status: WorldBookStatus = "draft"

    @field_validator(
        "name",
        "genre",
        "era_background",
        "world_rules",
        "organizations",
        "locations",
        "social_structure",
        "taboo_or_constraints",
        "tone_style",
        "summary",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理世界观资产文本字段，避免保存无意义空白。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class WorldBookCreate(WorldBookBase):
    """WorldBookCreate 创建请求体，用于约束接口数据结构。"""
    pass


class WorldBookUpdate(WorldBookBase):
    """WorldBookUpdate 更新请求体，用于约束接口数据结构。"""
    pass


class WorldBookResponse(WorldBookBase):
    """WorldBookResponse 响应体，用于约束接口数据结构。"""
    id: str
    version: int
    entry_count: int = 0
    active_entry_count: int = 0
    created_at: str
    updated_at: str


class WorldEntryBase(BaseModel):
    """WorldEntryBase 数据结构，定义接口层使用的数据字段。"""
    title: str = Field(min_length=1, max_length=120)
    entry_type: WorldEntryType = "世界规则"
    keywords: Optional[str] = None
    content: str = Field(min_length=1)
    applicable_scope: Optional[str] = "全局"
    priority: int = 0
    status: WorldEntryStatus = "active"

    @field_validator("title", "keywords", "content", "applicable_scope", mode="before")
    @classmethod
    def normalize_entry_text(cls, value: Optional[str]) -> Optional[str]:
        """清理世界观条目文本字段，保证关键词和内容可稳定进入项目快照。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class WorldEntryCreate(WorldEntryBase):
    """WorldEntryCreate 创建请求体，用于约束接口数据结构。"""
    pass


class WorldEntryUpdate(WorldEntryBase):
    """WorldEntryUpdate 更新请求体，用于约束接口数据结构。"""
    pass


class WorldEntryResponse(WorldEntryBase):
    """WorldEntryResponse 响应体，用于约束接口数据结构。"""
    id: str
    world_book_id: str
    created_at: str
    updated_at: str


class ProjectWorldSnapshotCreate(BaseModel):
    """ProjectWorldSnapshotCreate 创建请求体，用于约束接口数据结构。"""
    source_world_book_id: str = Field(min_length=1)
    load_mode: Literal["new", "replace"] = "new"
    replace_snapshot_id: Optional[str] = None


class ProjectWorldSnapshotUpdate(BaseModel):
    """ProjectWorldSnapshotUpdate 更新请求体，用于约束接口数据结构。"""
    name: str = Field(min_length=1, max_length=120)
    genre: str = Field(min_length=1, max_length=120)
    snapshot_content: str = Field(min_length=1)
    entry_snapshot_content: str = Field(min_length=1)

    @field_validator("name", "genre", "snapshot_content", "entry_snapshot_content", mode="before")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理项目世界观快照文本字段，只影响当前项目副本。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ProjectWorldSnapshotResponse(BaseModel):
    """ProjectWorldSnapshotResponse 响应体，用于约束接口数据结构。"""
    id: str
    project_id: str
    source_world_book_id: str
    source_version: int
    name: str
    genre: str
    snapshot_content: str
    entry_snapshot_content: str
    loaded_at: str
    updated_at: str


class ProjectArtifactBase(BaseModel):
    """ProjectArtifactBase 数据结构，定义接口层使用的数据字段。"""
    status: ProjectArtifactStatus = "draft"

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> str:
        """校验项目产物状态，缺省回到 draft 并限制为固定流转值。"""
        if not isinstance(value, str) or not value.strip():
            return "draft"
        status = value.strip()
        if status not in {"draft", "confirmed", "needs_review"}:
            raise ValueError("状态只能是 draft、confirmed 或 needs_review")
        return status


class ProjectStoryOutlinePayload(ProjectArtifactBase):
    """ProjectStoryOutlinePayload 业务请求体，用于约束接口数据结构。"""
    logline: Optional[str] = None
    story_background: Optional[str] = None
    core_conflict: Optional[str] = None
    main_goal: Optional[str] = None
    story_start: Optional[str] = None
    plot_structure: Optional[str] = None
    reversals: Optional[str] = None
    emotion_curve: Optional[str] = None
    foreshadowing: Optional[str] = None
    character_arcs: Optional[str] = None
    ending_direction: Optional[str] = None
    pacing_advice: Optional[str] = None
    capacity_advice: Optional[str] = None
    notes: Optional[str] = None

    @field_validator(
        "logline",
        "story_background",
        "core_conflict",
        "main_goal",
        "story_start",
        "plot_structure",
        "reversals",
        "emotion_curve",
        "foreshadowing",
        "character_arcs",
        "ending_direction",
        "pacing_advice",
        "capacity_advice",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理故事大纲字段，空白内容不参与后续生成上下文。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ProjectStoryOutlineResponse(ProjectStoryOutlinePayload):
    """ProjectStoryOutlineResponse 响应体，用于约束接口数据结构。"""
    id: str
    project_id: str
    created_at: str
    updated_at: str


class StoryOutlineGeneratePayload(BaseModel):
    """StoryOutlineGeneratePayload 业务请求体，用于约束接口数据结构。"""
    user_requirements: Optional[str] = None
    reference_draft_id: Optional[str] = None
    write_mode: StoryOutlineWriteMode = "preview"

    @field_validator("user_requirements", "reference_draft_id", mode="before")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理故事大纲生成参数，避免空白要求误导模型。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class StoryOutlineGenerationResult(BaseModel):
    """StoryOutlineGenerationResult 生成结果响应体，用于约束接口数据结构。"""
    outline: ProjectStoryOutlinePayload
    applied: bool
    saved_outline: Optional[ProjectStoryOutlineResponse] = None
    context_summary: str


class StoryOutlineRewritePayload(BaseModel):
    """StoryOutlineRewritePayload 业务请求体，用于约束接口数据结构。"""
    field: str = Field(min_length=1)
    current_value: str = Field(min_length=1)
    instruction: str = Field(min_length=1)
    write_mode: StoryOutlineWriteMode = "preview"

    @field_validator("field", "current_value", "instruction", mode="before")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理故事大纲局部改写参数，确保字段和值可被模型明确处理。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class StoryOutlineRewriteResult(BaseModel):
    """StoryOutlineRewriteResult 生成结果响应体，用于约束接口数据结构。"""
    field: str
    value: str
    applied: bool
    saved_outline: Optional[ProjectStoryOutlineResponse] = None


class StoryOutlineAssistMessage(BaseModel):
    """StoryOutlineAssistMessage 对话消息结构，用于约束接口数据结构。"""
    role: StoryOutlineAssistMessageRole
    content: str = Field(min_length=1)

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, value: Optional[str]) -> Optional[str]:
        """清理故事大纲辅助问答消息，空白消息不进入模型上下文。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class StoryOutlineAssistPatch(BaseModel):
    """StoryOutlineAssistPatch 局部更新结构，用于约束接口数据结构。"""
    logline: Optional[str] = None
    story_background: Optional[str] = None
    core_conflict: Optional[str] = None
    main_goal: Optional[str] = None
    story_start: Optional[str] = None
    plot_structure: Optional[str] = None
    reversals: Optional[str] = None
    emotion_curve: Optional[str] = None
    foreshadowing: Optional[str] = None
    character_arcs: Optional[str] = None
    ending_direction: Optional[str] = None
    pacing_advice: Optional[str] = None
    capacity_advice: Optional[str] = None
    notes: Optional[str] = None

    @field_validator(
        "logline",
        "story_background",
        "core_conflict",
        "main_goal",
        "story_start",
        "plot_structure",
        "reversals",
        "emotion_curve",
        "foreshadowing",
        "character_arcs",
        "ending_direction",
        "pacing_advice",
        "capacity_advice",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理故事大纲补丁字段，只保留模型明确给出的有效内容。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class StoryOutlineAssistPayload(BaseModel):
    """StoryOutlineAssistPayload 业务请求体，用于约束接口数据结构。"""
    action: StoryOutlineAssistAction
    current_outline: ProjectStoryOutlinePayload
    messages: list[StoryOutlineAssistMessage] = Field(default_factory=list)
    user_message: Optional[str] = None
    client_request_id: Optional[str] = None

    @field_validator("user_message", "client_request_id", mode="before")
    @classmethod
    def normalize_user_message(cls, value: Optional[str]) -> Optional[str]:
        """清理用户本轮问答内容和客户端请求编号。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class StoryOutlineAssistCompletion(BaseModel):
    """StoryOutlineAssistCompletion 完成度结构，用于约束接口数据结构。"""
    required_fields: list[str]
    completed_fields: list[str]
    missing_fields: list[str]
    is_complete: bool


class StoryOutlineAssistResult(BaseModel):
    """StoryOutlineAssistResult 生成结果响应体，用于约束接口数据结构。"""
    assistant_message: str
    outline_patch: StoryOutlineAssistPatch
    completion: StoryOutlineAssistCompletion
    field_notes: dict[str, str] = Field(default_factory=dict)
    next_focus_fields: list[str] = Field(default_factory=list)
    request_id: Optional[str] = None
    elapsed_ms: Optional[int] = None
    stage_timings: dict[str, int] = Field(default_factory=dict)


class ReferenceStoryStructureExtractPayload(BaseModel):
    """ReferenceStoryStructureExtractPayload 业务请求体，用于约束接口数据结构。"""
    source_type: ReferenceStorySourceType
    source_filename: Optional[str] = None
    source_text: str = Field(min_length=1)
    user_requirements: Optional[str] = None

    @field_validator("source_filename", "source_text", "user_requirements", mode="before")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理参考故事结构抽取字段，避免空白文件名或要求进入模型。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("source_filename")
    @classmethod
    def validate_source_filename(cls, value: Optional[str], info) -> Optional[str]:
        """校验上传参考故事文件名，第一期只允许 txt 或 md 文本。"""
        if info.data.get("source_type") == "uploaded":
            if not value:
                raise ValueError("上传参考故事时必须提供文件名")
            lowered = value.lower()
            if not lowered.endswith((".txt", ".md")):
                raise ValueError("第一版只支持 txt 或 md 文本文件")
        return value


class ReferenceStoryStructureDraftResponse(BaseModel):
    """ReferenceStoryStructureDraftResponse 响应体，用于约束接口数据结构。"""
    id: str
    project_id: str
    source_type: ReferenceStorySourceType
    source_filename: Optional[str]
    source_text_excerpt: Optional[str]
    story_type: Optional[str]
    goal_model: Optional[str]
    inciting_event_type: Optional[str]
    conflict_model: Optional[str]
    stage_structure: Optional[str]
    reversal_mechanism: Optional[str]
    emotion_curve: Optional[str]
    foreshadowing_pattern: Optional[str]
    ending_pattern: Optional[str]
    adaptation_advice: Optional[str]
    de_specificity_notes: Optional[str]
    validation_status: ReferenceStoryValidationStatus
    validation_notes: Optional[str]
    status: ReferenceStoryDraftStatus
    outline_preview: ProjectStoryOutlinePayload
    created_at: str
    updated_at: str


class ReferenceStoryStructureApplyPayload(BaseModel):
    """ReferenceStoryStructureApplyPayload 业务请求体，用于约束接口数据结构。"""
    apply_mode: ReferenceStoryApplyMode = "fill_empty"
    user_requirements: Optional[str] = None

    @field_validator("user_requirements", mode="before")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理参考结构应用要求，避免空白要求覆盖默认应用策略。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ProjectEpisodeOutlinePayload(ProjectArtifactBase):
    """ProjectEpisodeOutlinePayload 业务请求体，用于约束接口数据结构。"""
    title: Optional[str] = None
    synopsis: Optional[str] = None
    hook: Optional[str] = None
    conflict: Optional[str] = None
    reversal: Optional[str] = None
    cliffhanger: Optional[str] = None
    duration_minutes: Optional[float] = None

    @field_validator("title", "synopsis", "hook", "conflict", "reversal", "cliffhanger", mode="before")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理分集大纲文本字段，空白字段不写入剧情上下文。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration_minutes(cls, value: Optional[float]) -> Optional[float]:
        """校验分集预计时长必须为正数，避免无效制作节奏数据。"""
        if value is not None and value <= 0:
            raise ValueError("预计时长必须大于 0 分钟")
        return value


class ProjectEpisodeOutlineResponse(ProjectEpisodeOutlinePayload):
    """ProjectEpisodeOutlineResponse 响应体，用于约束接口数据结构。"""
    id: str
    project_id: str
    episode_no: int
    created_at: str
    updated_at: str


class ProjectEpisodeContentPayload(ProjectArtifactBase):
    """ProjectEpisodeContentPayload 业务请求体，用于约束接口数据结构。"""
    title: Optional[str] = None
    detailed_content: Optional[str] = None
    chapter_summary: Optional[str] = None
    hook: Optional[str] = None
    key_beats: Optional[str] = None
    previous_context_summary: Optional[str] = None
    quality_check_notes: Optional[str] = None

    @field_validator(
        "title",
        "detailed_content",
        "chapter_summary",
        "hook",
        "key_beats",
        "previous_context_summary",
        "quality_check_notes",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理单集正文字段，保证字数统计和上下文拼接基于有效内容。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ProjectEpisodeContentResponse(ProjectEpisodeContentPayload):
    """ProjectEpisodeContentResponse 响应体，用于约束接口数据结构。"""
    id: str
    project_id: str
    episode_no: int
    word_count: int
    created_at: str
    updated_at: str


class EpisodeContentGenerationCreate(BaseModel):
    """创建单集正文候选稿的请求。"""
    instruction: Optional[str] = None
    client_request_id: str = Field(min_length=1, max_length=80)
    generation_type: EpisodeContentGenerationType = "create"

    @field_validator("instruction", "client_request_id", mode="before")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class EpisodeContentGenerationUpdate(BaseModel):
    """保存用户对候选稿的编辑。"""
    output_text: str = Field(min_length=1)

    @field_validator("output_text", mode="before")
    @classmethod
    def normalize_output(cls, value: str) -> str:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
        raise ValueError("候选稿不能为空")


class EpisodeContentGenerationResponse(BaseModel):
    """单集正文候选版本响应。"""
    id: str
    project_id: str
    episode_no: int
    generation_type: EpisodeContentGenerationType
    instruction: Optional[str]
    input_snapshot: dict
    output_text: str
    word_count: int
    status: EpisodeContentGenerationStatus
    client_request_id: str
    model_config_id: Optional[str]
    model_name: Optional[str]
    elapsed_ms: Optional[int]
    created_at: str
    updated_at: str
    adopted_at: Optional[str]


class EpisodeContentGenerationAdoptResponse(BaseModel):
    """采用候选稿后的版本与正式正文。"""
    generation: EpisodeContentGenerationResponse
    content: ProjectEpisodeContentResponse


class ScriptBlockPayload(BaseModel):
    id: Optional[str] = None
    block_type: ScriptBlockType = "action"
    character_snapshot_id: Optional[str] = None
    temporary_speaker_name: Optional[str] = Field(default=None, max_length=120)
    content: Optional[str] = Field(default=None, max_length=10000)
    emotion: Optional[str] = Field(default=None, max_length=120)
    performance_note: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("temporary_speaker_name", "content", "emotion", "performance_note", mode="before")
    @classmethod
    def normalize_text(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class ScriptScenePayload(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = Field(default=None, max_length=120)
    location: Optional[str] = Field(default=None, max_length=120)
    time_of_day: Optional[ScriptTimeOfDay] = None
    interior_exterior: Optional[ScriptInteriorExterior] = None
    character_snapshot_ids: list[str] = Field(default_factory=list)
    manual_duration_seconds: Optional[float] = Field(default=None, gt=0, le=3600)
    story_purpose: Optional[str] = Field(default=None, max_length=1000)
    blocks: list[ScriptBlockPayload] = Field(default_factory=list, max_length=500)

    @field_validator("title", "location", "story_purpose", mode="before")
    @classmethod
    def normalize_text(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class ProjectEpisodeScriptPayload(BaseModel):
    """原子保存完整结构化剧本聚合。"""
    revision: Optional[int] = Field(default=None, ge=1)
    title: Optional[str] = Field(default=None, max_length=120)
    manual_duration_seconds: Optional[float] = Field(default=None, gt=0, le=3600)
    scenes: list[ScriptScenePayload] = Field(default_factory=list, max_length=200)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class ScriptBlockResponse(ScriptBlockPayload):
    id: str
    scene_id: str
    sort_order: int
    created_at: str
    updated_at: str


class ScriptCharacterRef(BaseModel):
    character_snapshot_id: str
    name: str
    updated_at: str


class ScriptSceneResponse(ScriptScenePayload):
    id: str
    script_id: str
    scene_no: int
    character_refs: list[ScriptCharacterRef]
    auto_duration_seconds: float
    effective_duration_seconds: float
    sort_order: int
    blocks: list[ScriptBlockResponse]
    created_at: str
    updated_at: str


class ScriptCheckIssue(BaseModel):
    code: str
    severity: Literal["error", "warning", "info"]
    message: str
    scene_id: Optional[str] = None
    block_id: Optional[str] = None
    details: dict = Field(default_factory=dict)


class ProjectEpisodeScriptResponse(BaseModel):
    id: str
    project_id: str
    episode_no: int
    title: Optional[str]
    revision: int
    version: int
    source_content_version: Optional[str]
    auto_duration_seconds: float
    manual_duration_seconds: Optional[float]
    effective_duration_seconds: float
    target_duration_seconds: float
    duration_deviation_seconds: float
    duration_deviation_percent: float
    status: ScriptStatus
    confirmed_at: Optional[str]
    scenes: list[ScriptSceneResponse]
    validation_issues: list[ScriptCheckIssue]
    created_at: str
    updated_at: str


class ScriptGenerationCreate(BaseModel):
    generation_scope: ScriptGenerationScope
    target_scene_id: Optional[str] = None
    target_block_ids: list[str] = Field(default_factory=list)
    rewrite_preset: Optional[ScriptRewritePreset] = None
    instruction: Optional[str] = Field(default=None, max_length=2000)
    client_request_id: str = Field(min_length=1, max_length=80)
    base_script_version: Optional[int] = None
    base_script_revision: Optional[int] = None

    @field_validator("instruction", "client_request_id", mode="before")
    @classmethod
    def normalize_text(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class ScriptGenerationResponse(BaseModel):
    id: str
    project_id: str
    episode_no: int
    generation_scope: ScriptGenerationScope
    target_scene_id: Optional[str]
    target_block_ids: list[str]
    rewrite_preset: Optional[ScriptRewritePreset]
    instruction: Optional[str]
    base_script_version: Optional[int]
    base_script_revision: Optional[int]
    input_snapshot: dict
    output_snapshot: dict
    status: ScriptGenerationStatus
    client_request_id: str
    model_config_id: Optional[str]
    model_name: Optional[str]
    elapsed_ms: Optional[int]
    adopted_at: Optional[str]
    created_at: str
    updated_at: str


class ScriptRevisionPayload(BaseModel):
    revision: Optional[int] = None


class ScriptCheckPayload(BaseModel):
    revision: int = Field(ge=1)
    mode: Literal["structure", "full"] = "full"


class ScriptCheckResponse(BaseModel):
    id: str
    script_id: str
    script_version: int
    script_revision: int
    mode: Literal["structure", "full"]
    semantic_check_status: Literal["not_requested", "succeeded", "failed"]
    issues: list[ScriptCheckIssue]
    model_config_id: Optional[str]
    model_name: Optional[str]
    created_at: str


class ScriptGenerationAdoptResponse(BaseModel):
    generation: ScriptGenerationResponse
    script: ProjectEpisodeScriptResponse


class ScriptVersionSummary(BaseModel):
    version: int
    source_content_version: Optional[str]
    change_source: str
    generation_id: Optional[str]
    duration_seconds: float
    scene_count: int
    created_at: str


class ShotPromptPayload(BaseModel):
    image_prompt: Optional[str] = None
    video_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    first_frame_description: Optional[str] = None
    last_frame_description: Optional[str] = None
    reference_asset_ids: list[str] = Field(default_factory=list)
    aspect_ratio: Optional[str] = None
    seedance_prompt: Optional[str] = None

    @field_validator(
        "image_prompt", "video_prompt", "negative_prompt", "first_frame_description",
        "last_frame_description", "aspect_ratio", "seedance_prompt", mode="before",
    )
    @classmethod
    def normalize_prompt_text(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class ProjectStoryboardShotPayload(BaseModel):
    """镜头编辑载荷；编号和排序由服务端维护。"""
    revision: Optional[int] = Field(default=None, ge=1)
    source_scene_id: Optional[str] = None
    shot_size: Optional[str] = Field(default=None, max_length=40)
    subject_description: Optional[str] = None
    visual_description: Optional[str] = None
    action: Optional[str] = None
    duration_seconds: Optional[float] = Field(default=None, gt=0)
    camera_angle: Optional[str] = None
    camera_movement: Optional[str] = None
    composition: Optional[str] = None
    character_snapshot_ids: list[str] = Field(default_factory=list)
    expression: Optional[str] = None
    environment: Optional[str] = None
    props: list[str] = Field(default_factory=list)
    source_block_ids: list[str] = Field(default_factory=list)
    dialogue_snapshot: Optional[str] = None
    voiceover_snapshot: Optional[str] = None
    sound_effect: Optional[str] = None
    music_note: Optional[str] = None
    continuity_note: Optional[str] = None
    status: StoryboardStatus = "draft"
    prompt: ShotPromptPayload = Field(default_factory=ShotPromptPayload)
    # 兼容旧客户端；新工作台不提交以下字段。
    shot_no: Optional[int] = Field(default=None, ge=1)
    scene: Optional[str] = None
    visual_prompt: Optional[str] = None
    camera: Optional[str] = None
    dialogue_or_voiceover: Optional[str] = None

    @field_validator(
        "shot_size", "subject_description", "visual_description", "action", "camera_angle",
        "camera_movement", "composition", "expression", "environment", "dialogue_snapshot",
        "voiceover_snapshot", "sound_effect", "music_note", "continuity_note", "scene",
        "visual_prompt", "camera", "dialogue_or_voiceover", mode="before",
    )
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理分镜文本字段，保证镜头提示词和对白信息可直接用于制作。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("duration_seconds")
    @classmethod
    def validate_duration_seconds(cls, value: Optional[float]) -> Optional[float]:
        """校验镜头时长必须为正数，避免生成无效分镜节奏。"""
        if value is not None and value <= 0:
            raise ValueError("镜头时长必须大于 0 秒")
        return value


class ProjectStoryboardShotResponse(ProjectStoryboardShotPayload):
    """ProjectStoryboardShotResponse 响应体，用于约束接口数据结构。"""
    id: str
    project_id: str
    episode_no: int
    storyboard_id: str
    source_scene_id: Optional[str]
    display_code: str
    sort_order: int
    revision: int
    source_status: StoryboardSourceStatus
    prompt_freshness: Literal["current", "needs_update"]
    prompt_customized: bool
    created_at: str
    updated_at: str


class StoryboardSceneGroupResponse(BaseModel):
    scene_id: Optional[str]
    scene_no: Optional[int]
    display_code: str
    title: str
    script_duration_seconds: Optional[float]
    shots_duration_seconds: float
    duration_deviation_percent: Optional[float]
    status: StoryboardStatus
    shots: list[ProjectStoryboardShotResponse]


class ProjectStoryboardResponse(BaseModel):
    id: str
    project_id: str
    episode_no: int
    version: int
    revision: int
    source_script_id: Optional[str]
    source_script_version: Optional[int]
    source_script_status: Optional[str]
    total_duration_seconds: float
    status: StoryboardStatus
    shot_count: int
    scene_groups: list[StoryboardSceneGroupResponse]
    created_at: str
    updated_at: str


class StoryboardReorderPayload(BaseModel):
    shot_ids: list[str] = Field(min_length=1)


class StoryboardReassignPayload(BaseModel):
    source_scene_id: str


class StoryboardDuplicatePayload(BaseModel):
    target_scene_id: Optional[str] = None


class ShotVideoGenerationCreatePayload(BaseModel):
    resolution: Optional[str] = None
    aspect_ratio: Optional[str] = None
    duration_seconds: Optional[float] = Field(default=None, gt=0, le=60)

    @field_validator("resolution", "aspect_ratio", mode="before")
    @classmethod
    def normalize_generation_option(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in {"720p", "1080p"}:
            raise ValueError("视频分辨率仅支持 720p 或 1080p")
        return value

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in {"16:9", "9:16", "1:1", "4:3", "3:4", "21:9"}:
            raise ValueError("视频画幅不支持")
        return value


class ShotVideoGenerationResponse(BaseModel):
    id: str
    project_id: str
    episode_no: int
    storyboard_id: str
    shot_id: str
    prompt_id: Optional[str]
    source_shot_revision: int
    source_prompt_revision: Optional[int]
    video_prompt_snapshot: str
    negative_prompt_snapshot: Optional[str]
    reference_asset_ids: list[str]
    model_config_id: str
    model_name: str
    provider_preset: Optional[str]
    provider_task_id: Optional[str]
    status: ShotVideoGenerationStatus
    result_url: Optional[str]
    local_asset_path: Optional[str]
    thumbnail_url: Optional[str]
    duration_seconds: Optional[float]
    width: Optional[int]
    height: Optional[int]
    error_message: Optional[str]
    request_payload_snapshot: dict[str, object]
    elapsed_ms: Optional[int]
    adopted: bool
    adopted_at: Optional[str]
    is_stale: bool
    created_at: str
    updated_at: str


class ProjectCopywritingPayload(ProjectArtifactBase):
    """ProjectCopywritingPayload 业务请求体，用于约束接口数据结构。"""
    subtitles: Optional[str] = None
    platform_title: Optional[str] = None
    platform_description: Optional[str] = None
    publish_copy: Optional[str] = None

    @field_validator("subtitles", "platform_title", "platform_description", "publish_copy", mode="before")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        """清理发布文案字段，空白字幕或文案不保存为有效内容。"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ProjectCopywritingResponse(ProjectCopywritingPayload):
    """ProjectCopywritingResponse 响应体，用于约束接口数据结构。"""
    id: str
    project_id: str
    episode_no: int
    created_at: str
    updated_at: str
