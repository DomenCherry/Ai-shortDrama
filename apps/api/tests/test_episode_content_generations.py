import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch


os.environ["API_DATABASE_URL"] = "sqlite://"

from app.core.config import get_settings
from app.core.db import Base, get_engine, get_session, get_session_factory
from app.models.db_models import (
    Project,
    ProjectEpisodeContent,
    ProjectEpisodeOutline,
    ProjectEpisodeScript,
    ProjectStoryOutline,
)
from app.models.schemas import EpisodeContentGenerationCreate, EpisodeContentGenerationUpdate, ProjectEpisodeContentPayload
from app.services.project.story import episode_contents


class EpisodeContentGenerationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["API_DATABASE_URL"] = f"sqlite:///{self.temp_dir.name}/test.db"
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        Base.metadata.create_all(bind=get_engine())
        self.project_id = "project-1"
        self._seed_story()

    def tearDown(self) -> None:
        get_session_factory.cache_clear()
        get_engine.cache_clear()
        get_settings.cache_clear()
        self.temp_dir.cleanup()

    def _seed_story(self) -> None:
        now = datetime.now(timezone.utc)
        with get_session() as session:
            session.add(
                Project(
                    id=self.project_id,
                    title="测试短剧",
                    idea="女主追查失踪案",
                    target_platform="抖音",
                    genre="悬疑",
                    episode_count=2,
                    episode_duration=1,
                    total_duration=2,
                    target_audience="悬疑短剧观众",
                    style="紧凑写实",
                    status="draft",
                    created_at=now,
                    updated_at=now,
                )
            )
            session.add(
                ProjectStoryOutline(
                    id="story-1",
                    project_id=self.project_id,
                    logline="记者追查好友失踪真相。",
                    status="confirmed",
                    created_at=now,
                    updated_at=now,
                )
            )
            session.add_all(
                [
                    ProjectEpisodeOutline(
                        id="outline-1",
                        project_id=self.project_id,
                        episode_no=1,
                        title="消失的留言",
                        synopsis="记者发现好友留下的异常语音。",
                        hook="凌晨收到好友语音。",
                        conflict="语音内容与警方结论冲突。",
                        reversal="语音发送时间晚于失踪时间。",
                        cliffhanger="门外响起好友熟悉的敲门节奏。",
                        duration_minutes=1,
                        status="confirmed",
                        created_at=now,
                        updated_at=now,
                    ),
                    ProjectEpisodeOutline(
                        id="outline-2",
                        project_id=self.project_id,
                        episode_no=2,
                        title="门外的人",
                        synopsis="记者追查敲门者。",
                        hook="猫眼里没有人。",
                        conflict="楼道监控被人为删除。",
                        reversal="删除者使用了好友账号。",
                        cliffhanger="好友账号突然发来实时定位。",
                        duration_minutes=1,
                        status="confirmed",
                        created_at=now,
                        updated_at=now,
                    ),
                ]
            )
            session.add(
                ProjectEpisodeContent(
                    id="content-1",
                    project_id=self.project_id,
                    episode_no=1,
                    detailed_content="第一集旧正文",
                    chapter_summary="记者收到失踪好友的异常语音。",
                    quality_check_notes="旧质检",
                    word_count=7,
                    status="confirmed",
                    created_at=now,
                    updated_at=now,
                )
            )
            session.add(
                ProjectEpisodeScript(
                    id="script-2",
                    project_id=self.project_id,
                    episode_no=2,
                    scene_text="旧剧本",
                    status="confirmed",
                    created_at=now,
                    updated_at=now,
                )
            )

    async def _generate(self, request_id: str = "request-1") -> dict:
        model_config = {
            "id": "model-1",
            "model_name": "test-model",
            "last_test_status": "success",
        }
        with (
            patch.object(episode_contents.model_configs, "get_enabled_config", return_value=model_config),
            patch.object(
                episode_contents,
                "call_text_generation_api",
                new=AsyncMock(return_value={"detailed_content": "门外的脚步突然停住，手机同时亮起。"}),
            ) as model_call,
        ):
            generated = await episode_contents.generate_episode_content(
                self.project_id,
                2,
                EpisodeContentGenerationCreate(instruction="加强压迫感", client_request_id=request_id),
            )
            duplicate = await episode_contents.generate_episode_content(
                self.project_id,
                2,
                EpisodeContentGenerationCreate(instruction="加强压迫感", client_request_id=request_id),
            )
        self.assertEqual(model_call.await_count, 1)
        self.assertEqual(generated["id"], duplicate["id"])
        return generated

    async def test_generation_is_idempotent_and_preserves_formal_content(self) -> None:
        generated = await self._generate()

        self.assertEqual(generated["status"], "candidate")
        self.assertEqual(generated["input_snapshot"]["episode_outline"]["episode_no"], 2)
        self.assertEqual(
            generated["input_snapshot"]["previous_episode_summary"],
            "记者收到失踪好友的异常语音。",
        )
        self.assertEqual(generated["input_snapshot"]["target_chinese_characters"], {"min": 600, "max": 900})
        self.assertIsNone(episode_contents.get_episode_content(self.project_id, 2))

    async def test_edit_and_adopt_candidate_updates_content_and_downstream_status(self) -> None:
        generated = await self._generate()
        stale_candidate = await self._generate("request-2")
        edited = episode_contents.update_episode_content_generation(
            self.project_id,
            2,
            generated["id"],
            EpisodeContentGenerationUpdate(output_text="门外无人，手机却收到了好友的实时定位。"),
        )
        result = episode_contents.adopt_episode_content_generation(self.project_id, 2, edited["id"])

        self.assertEqual(result["generation"]["status"], "adopted")
        self.assertEqual(result["content"]["detailed_content"], "门外无人，手机却收到了好友的实时定位。")
        self.assertEqual(result["content"]["status"], "draft")
        self.assertIsNone(result["content"]["chapter_summary"])
        self.assertIsNone(result["content"]["quality_check_notes"])
        history = episode_contents.list_episode_content_generations(self.project_id, 2)
        stale = next(item for item in history if item["id"] == stale_candidate["id"])
        self.assertEqual(stale["status"], "discarded")
        with get_session() as session:
            script = session.get(ProjectEpisodeScript, "script-2")
            self.assertEqual(script.status, "needs_review")

    async def test_adopt_rejects_candidate_when_formal_content_changed(self) -> None:
        generated = await self._generate()
        episode_contents.upsert_episode_content(
            self.project_id,
            2,
            ProjectEpisodeContentPayload(detailed_content="人工刚写的新正文", status="draft"),
        )

        with self.assertRaisesRegex(ValueError, "当前正文已在候选稿生成后更新"):
            episode_contents.adopt_episode_content_generation(self.project_id, 2, generated["id"])

    async def test_generation_reports_missing_model_configuration(self) -> None:
        with patch.object(episode_contents.model_configs, "get_enabled_config", return_value=None):
            with self.assertRaisesRegex(ValueError, "请先配置并测试成功文本生成模型 API"):
                await episode_contents.generate_episode_content(
                    self.project_id,
                    2,
                    EpisodeContentGenerationCreate(client_request_id="missing-model"),
                )

    async def test_generation_rejects_empty_model_output(self) -> None:
        model_config = {"id": "model-1", "model_name": "test-model", "last_test_status": "success"}
        with (
            patch.object(episode_contents.model_configs, "get_enabled_config", return_value=model_config),
            patch.object(
                episode_contents,
                "call_text_generation_api",
                new=AsyncMock(return_value={"detailed_content": ""}),
            ),
        ):
            with self.assertRaisesRegex(ValueError, "正文生成结果为空"):
                await episode_contents.generate_episode_content(
                    self.project_id,
                    2,
                    EpisodeContentGenerationCreate(client_request_id="empty-output"),
                )


if __name__ == "__main__":
    unittest.main()
