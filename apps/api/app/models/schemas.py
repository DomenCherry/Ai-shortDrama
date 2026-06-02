from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


ConfigType = Literal["text", "image"]
ProviderMode = Literal["preset", "custom"]
CharacterGender = Literal["男", "女"]
CharacterCardStatus = Literal["draft", "active", "archived"]
WorldBookStatus = Literal["draft", "active", "archived"]
WorldEntryStatus = Literal["active", "disabled"]
WorldEntryType = Literal["世界规则", "地点", "组织", "阶层关系", "历史事件", "特殊物品", "禁忌或限制", "风格约束", "其他"]
ProjectArtifactStatus = Literal["draft", "confirmed", "needs_review"]


class ModelApiConfigCreate(BaseModel):
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
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ModelApiConfigUpdate(BaseModel):
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
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ModelApiConfigResponse(BaseModel):
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
    success: bool
    status: str
    message: str
    latency_ms: Optional[int] = None
    tested_at: str


class ProjectCreate(BaseModel):
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
        if not isinstance(value, str) or not value.strip():
            raise ValueError("请先输入短剧创意描述")
        return value.strip()

    @field_validator("episode_count")
    @classmethod
    def validate_episode_count(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("集数必须是大于 0 的整数")
        return value

    @field_validator("episode_duration")
    @classmethod
    def validate_episode_duration(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("单集时长必须大于 0 分钟")
        if value > 2:
            raise ValueError("单集时长不能超过 2 分钟")
        return value


class ProjectUpdate(ProjectCreate):
    pass


class ProjectResponse(BaseModel):
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
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("gender", mode="before")
    @classmethod
    def validate_gender(cls, value: Optional[str]) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("性别不能为空")
        gender = value.strip()
        if gender not in {"男", "女"}:
            raise ValueError("性别只能选择男或女")
        return gender


class CharacterCardCreate(CharacterCardBase):
    pass


class CharacterCardUpdate(CharacterCardBase):
    pass


class CharacterCardResponse(CharacterCardBase):
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
    filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    data_url: str = Field(min_length=1)


class CharacterImageAssetResponse(BaseModel):
    character_card_id: str
    image_url: str
    local_path: str
    updated_at: str


class CharacterTurnaroundGenerate(BaseModel):
    prompt: Optional[str] = None


class CharacterTurnaroundResponse(BaseModel):
    character_card_id: str
    image_url: Optional[str] = None
    local_path: Optional[str] = None
    generation_prompt: Optional[str] = None
    status: str
    version: int
    confirmed_at: Optional[str] = None
    updated_at: str


class ProjectCharacterSnapshotCreate(BaseModel):
    source_character_card_id: str = Field(min_length=1)
    load_mode: Literal["new", "replace"] = "new"
    replace_snapshot_id: Optional[str] = None


class ProjectCharacterSnapshotResponse(BaseModel):
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
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class WorldBookCreate(WorldBookBase):
    pass


class WorldBookUpdate(WorldBookBase):
    pass


class WorldBookResponse(WorldBookBase):
    id: str
    version: int
    entry_count: int = 0
    active_entry_count: int = 0
    created_at: str
    updated_at: str


class WorldEntryBase(BaseModel):
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
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class WorldEntryCreate(WorldEntryBase):
    pass


class WorldEntryUpdate(WorldEntryBase):
    pass


class WorldEntryResponse(WorldEntryBase):
    id: str
    world_book_id: str
    created_at: str
    updated_at: str


class ProjectWorldSnapshotCreate(BaseModel):
    source_world_book_id: str = Field(min_length=1)
    load_mode: Literal["new", "replace"] = "new"
    replace_snapshot_id: Optional[str] = None


class ProjectWorldSnapshotResponse(BaseModel):
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
    status: ProjectArtifactStatus = "draft"

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> str:
        if not isinstance(value, str) or not value.strip():
            return "draft"
        status = value.strip()
        if status not in {"draft", "confirmed", "needs_review"}:
            raise ValueError("状态只能是 draft、confirmed 或 needs_review")
        return status


class ProjectStoryOutlinePayload(ProjectArtifactBase):
    logline: Optional[str] = None
    core_conflict: Optional[str] = None
    main_goal: Optional[str] = None
    character_arcs: Optional[str] = None
    ending_direction: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("logline", "core_conflict", "main_goal", "character_arcs", "ending_direction", "notes", mode="before")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ProjectStoryOutlineResponse(ProjectStoryOutlinePayload):
    id: str
    project_id: str
    created_at: str
    updated_at: str


class ProjectEpisodeOutlinePayload(ProjectArtifactBase):
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
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration_minutes(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value <= 0:
            raise ValueError("预计时长必须大于 0 分钟")
        return value


class ProjectEpisodeOutlineResponse(ProjectEpisodeOutlinePayload):
    id: str
    project_id: str
    episode_no: int
    created_at: str
    updated_at: str


class ProjectEpisodeContentPayload(ProjectArtifactBase):
    detailed_content: Optional[str] = None
    key_beats: Optional[str] = None

    @field_validator("detailed_content", "key_beats", mode="before")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ProjectEpisodeContentResponse(ProjectEpisodeContentPayload):
    id: str
    project_id: str
    episode_no: int
    created_at: str
    updated_at: str


class ProjectEpisodeScriptPayload(ProjectArtifactBase):
    scene_text: Optional[str] = None
    dialogue: Optional[str] = None
    action_notes: Optional[str] = None
    voiceover: Optional[str] = None

    @field_validator("scene_text", "dialogue", "action_notes", "voiceover", mode="before")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ProjectEpisodeScriptResponse(ProjectEpisodeScriptPayload):
    id: str
    project_id: str
    episode_no: int
    created_at: str
    updated_at: str


class ProjectStoryboardShotPayload(ProjectArtifactBase):
    shot_no: int = Field(ge=1)
    scene: Optional[str] = None
    visual_prompt: Optional[str] = None
    camera: Optional[str] = None
    duration_seconds: Optional[float] = None
    dialogue_or_voiceover: Optional[str] = None

    @field_validator("scene", "visual_prompt", "camera", "dialogue_or_voiceover", mode="before")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("duration_seconds")
    @classmethod
    def validate_duration_seconds(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value <= 0:
            raise ValueError("镜头时长必须大于 0 秒")
        return value


class ProjectStoryboardShotResponse(ProjectStoryboardShotPayload):
    id: str
    project_id: str
    episode_no: int
    created_at: str
    updated_at: str


class ProjectCopywritingPayload(ProjectArtifactBase):
    subtitles: Optional[str] = None
    platform_title: Optional[str] = None
    platform_description: Optional[str] = None
    publish_copy: Optional[str] = None

    @field_validator("subtitles", "platform_title", "platform_description", "publish_copy", mode="before")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ProjectCopywritingResponse(ProjectCopywritingPayload):
    id: str
    project_id: str
    episode_no: int
    created_at: str
    updated_at: str
