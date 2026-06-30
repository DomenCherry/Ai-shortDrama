import os
import asyncio
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import httpx
from sqlalchemy import event


os.environ["API_DATABASE_URL"] = "sqlite://"

from app.core.config import get_settings
from app.core.db import Base, get_engine, get_session, get_session_factory
from app.models.db_models import CharacterCard, ModelApiConfig, Project, ProjectCharacterSnapshot
from app.models.schemas import (
    ProjectEpisodeScriptPayload,
    ProjectStoryboardShotPayload,
    ShotPromptPayload,
    ShotVideoGenerationCreatePayload,
    StoryboardDuplicatePayload,
    StoryboardReassignPayload,
    StoryboardReorderPayload,
)
from app.services.project.production import shot_videos, storyboard
from app.services.project.story import episode_scripts


class _FakeVideoClient:
    def __init__(self, post_data: dict | None = None, get_data: dict | None = None) -> None:
        self.post_data = post_data or {"id": "video-task", "status": "queued"}
        self.get_data = get_data or {"id": "video-task", "status": "succeeded", "data": [{"url": "https://cdn.test/video.mp4"}]}
        self.posts: list[dict] = []
        self.gets: list[dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def post(self, url: str, *, json: dict, headers: dict) -> httpx.Response:
        self.posts.append({"url": url, "json": json, "headers": headers})
        request = httpx.Request("POST", url)
        return httpx.Response(200, json=self.post_data, request=request)

    async def get(self, url: str, *, headers: dict) -> httpx.Response:
        self.gets.append({"url": url, "headers": headers})
        request = httpx.Request("GET", url)
        return httpx.Response(200, json=self.get_data, request=request)


class StoryboardAggregateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["API_DATABASE_URL"] = f"sqlite:///{self.temp_dir.name}/test.db"
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        engine = get_engine()

        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(bind=engine)
        now = datetime.now(timezone.utc)
        with get_session() as session:
            session.add(Project(
                id="project-storyboard", title="分镜测试", idea="测试", episode_count=2,
                episode_duration=1, total_duration=2, status="draft", created_at=now, updated_at=now,
            ))
            session.add(CharacterCard(
                id="character", name="林晚", gender="女", role_type="主角", identity="记者",
                goal="找到遗嘱", status="active",
                created_at=now, updated_at=now,
            ))
            session.add(ProjectCharacterSnapshot(
                id="snapshot", project_id="project-storyboard", source_character_card_id="character",
                source_version=1, name="林晚", gender="女", role_type="主角", snapshot_content="{}",
                loaded_at=now, updated_at=now,
            ))
            session.add(ModelApiConfig(
                id="video-config", config_type="video", provider_mode="preset",
                provider_preset="volcengine_seedance_1_5", provider_name="火山方舟",
                api_base_url="https://ark.test/api/v3", api_key_secret="video-secret",
                model_name="seedance-model", endpoint_path="/contents/generations/tasks",
                supports_reference_image=False, enabled=True, last_test_status="success",
                created_at=now, updated_at=now,
            ))
        script = episode_scripts.upsert_episode_script("project-storyboard", 1, ProjectEpisodeScriptPayload.model_validate({
            "revision": None,
            "scenes": [
                {"title": "客厅对峙", "location": "客厅", "character_snapshot_ids": ["snapshot"], "blocks": [{"block_type": "action", "content": "林晚推门。"}]},
                {"title": "走廊追逐", "location": "走廊", "character_snapshot_ids": ["snapshot"], "blocks": [{"block_type": "action", "content": "林晚追出去。"}]},
            ],
        }))
        self.scene_a = script["scenes"][0]["id"]
        self.scene_b = script["scenes"][1]["id"]

    def tearDown(self) -> None:
        get_session_factory.cache_clear()
        get_engine.cache_clear()
        get_settings.cache_clear()
        self.temp_dir.cleanup()

    def payload(self, scene_id: str | None, subject: str) -> ProjectStoryboardShotPayload:
        return ProjectStoryboardShotPayload(
            source_scene_id=scene_id, shot_size="中景", subject_description=subject,
            visual_description=f"{subject}进入画面", duration_seconds=3,
            character_snapshot_ids=["snapshot"], props=[], source_block_ids=[], status="draft",
            prompt=ShotPromptPayload(image_prompt=f"{subject}，电影感", video_prompt=f"{subject}走入画面", seedance_prompt=f"Seedance {subject}走入画面"),
        )

    def test_grouped_crud_reorder_reassign_and_stable_codes(self) -> None:
        first = storyboard.create_storyboard_shot("project-storyboard", 1, self.payload(self.scene_a, "林晚"))
        second = storyboard.create_storyboard_shot("project-storyboard", 1, self.payload(self.scene_a, "管家"))
        third = storyboard.create_storyboard_shot("project-storyboard", 1, self.payload(self.scene_b, "遗嘱"))
        self.assertEqual([first["display_code"], second["display_code"], third["display_code"]], ["S01-001", "S01-002", "S02-001"])

        reordered = storyboard.reorder_storyboard_scene(
            "project-storyboard", 1, self.scene_a, StoryboardReorderPayload(shot_ids=[second["id"], first["id"]])
        )
        self.assertEqual([shot["id"] for shot in reordered["scene_groups"][0]["shots"]], [second["id"], first["id"]])
        self.assertEqual(reordered["scene_groups"][0]["shots"][0]["display_code"], "S01-001")

        moved = storyboard.reassign_storyboard_shot(
            "project-storyboard", 1, first["id"], StoryboardReassignPayload(source_scene_id=self.scene_b)
        )
        self.assertEqual(moved["id"], first["id"])
        self.assertEqual(moved["display_code"], "S02-002")

        duplicate = storyboard.duplicate_storyboard_shot(
            "project-storyboard", 1, moved["id"], StoryboardDuplicatePayload(target_scene_id=self.scene_b)
        )
        self.assertNotEqual(duplicate["id"], moved["id"])
        aggregate = storyboard.get_storyboard("project-storyboard", 1)
        self.assertEqual(aggregate["shot_count"], 4)
        self.assertEqual(aggregate["version"], 6)

    def test_unassigned_shot_is_isolated_and_marked_for_review(self) -> None:
        shot = storyboard.create_storyboard_shot("project-storyboard", 1, self.payload(None, "旧镜头"))
        aggregate = storyboard.get_storyboard("project-storyboard", 1)
        group = aggregate["scene_groups"][-1]
        self.assertEqual(group["display_code"], "U")
        self.assertEqual(group["status"], "needs_review")
        self.assertEqual(shot["source_status"], "unassigned")

    def test_revision_conflict_does_not_overwrite(self) -> None:
        shot = storyboard.create_storyboard_shot("project-storyboard", 1, self.payload(self.scene_a, "林晚"))
        missing_revision = self.payload(self.scene_a, "缺少修订号")
        with self.assertRaisesRegex(storyboard.StoryboardConflictError, "缺少镜头修订号"):
            storyboard.update_storyboard_shot("project-storyboard", 1, shot["id"], missing_revision)

        payload = self.payload(self.scene_a, "改写")
        payload.revision = shot["revision"] + 1
        with self.assertRaises(storyboard.StoryboardConflictError):
            storyboard.update_storyboard_shot("project-storyboard", 1, shot["id"], payload)

    def test_legacy_update_preserves_aggregate_fields(self) -> None:
        shot = storyboard.create_storyboard_shot("project-storyboard", 1, self.payload(self.scene_a, "林晚"))
        legacy = ProjectStoryboardShotPayload.model_validate({
            "shot_no": 1, "scene": "客厅近景", "visual_prompt": "低照度客厅",
            "duration_seconds": 4, "status": "draft", "revision": shot["revision"],
        })
        updated = storyboard.update_storyboard_shot("project-storyboard", 1, shot["id"], legacy)
        self.assertEqual(updated["source_scene_id"], self.scene_a)
        self.assertEqual(updated["subject_description"], "林晚")
        self.assertEqual(updated["prompt"]["image_prompt"], "低照度客厅")

    def test_shot_video_generation_create_refresh_and_adopt(self) -> None:
        shot = storyboard.create_storyboard_shot("project-storyboard", 1, self.payload(self.scene_a, "林晚"))
        fake_client = _FakeVideoClient(
            post_data={"id": "seedance-task-1", "status": "queued"},
            get_data={
                "id": "seedance-task-1", "status": "succeeded",
                "data": [{"url": "https://cdn.test/video.mp4", "duration": 3, "width": 1280, "height": 720}],
            },
        )

        with patch.object(shot_videos.httpx, "AsyncClient", return_value=fake_client):
            created = asyncio.run(shot_videos.create_video_generation("project-storyboard", 1, shot["id"]))
            refreshed = asyncio.run(shot_videos.refresh_video_generation("project-storyboard", 1, shot["id"], created["id"]))

        self.assertEqual(created["provider_task_id"], "seedance-task-1")
        self.assertEqual(created["status"], "running")
        self.assertEqual(created["video_prompt_snapshot"], "Seedance 林晚走入画面")
        self.assertEqual(fake_client.posts[0]["url"], "https://ark.test/api/v3/contents/generations/tasks")
        self.assertEqual(fake_client.posts[0]["json"]["content"][0]["text"], "Seedance 林晚走入画面")
        self.assertEqual(fake_client.posts[0]["json"]["resolution"], "720p")
        self.assertEqual(fake_client.posts[0]["json"]["ratio"], "16:9")
        self.assertEqual(fake_client.posts[0]["json"]["duration"], 3)
        self.assertEqual(refreshed["status"], "succeeded")
        self.assertEqual(refreshed["result_url"], "https://cdn.test/video.mp4")

        adopted = shot_videos.adopt_video_generation("project-storyboard", 1, shot["id"], created["id"])
        self.assertTrue(adopted["adopted"])
        self.assertFalse(adopted["is_stale"])

    def test_shot_video_generation_accepts_per_request_options(self) -> None:
        shot = storyboard.create_storyboard_shot("project-storyboard", 1, self.payload(self.scene_a, "林晚"))
        fake_client = _FakeVideoClient(post_data={"id": "seedance-task-options", "status": "queued"})

        with patch.object(shot_videos.httpx, "AsyncClient", return_value=fake_client):
            created = asyncio.run(shot_videos.create_video_generation(
                "project-storyboard",
                1,
                shot["id"],
                ShotVideoGenerationCreatePayload(resolution="1080p", aspect_ratio="9:16", duration_seconds=6),
            ))

        self.assertEqual(created["provider_task_id"], "seedance-task-options")
        self.assertEqual(fake_client.posts[0]["json"]["resolution"], "1080p")
        self.assertEqual(fake_client.posts[0]["json"]["ratio"], "9:16")
        self.assertEqual(fake_client.posts[0]["json"]["duration"], 6)
        self.assertEqual(created["request_payload_snapshot"]["resolution"], "1080p")
        self.assertEqual(created["request_payload_snapshot"]["ratio"], "9:16")

    def test_delete_shot_with_video_generation_is_blocked(self) -> None:
        shot = storyboard.create_storyboard_shot("project-storyboard", 1, self.payload(self.scene_a, "林晚"))
        fake_client = _FakeVideoClient(post_data={"id": "seedance-task-delete", "status": "queued"})
        with patch.object(shot_videos.httpx, "AsyncClient", return_value=fake_client):
            asyncio.run(shot_videos.create_video_generation("project-storyboard", 1, shot["id"]))

        with self.assertRaisesRegex(ValueError, "镜头已有视频生成记录"):
            storyboard.delete_storyboard_shot("project-storyboard", 1, shot["id"])

        generations = shot_videos.list_video_generations("project-storyboard", 1, shot["id"])
        self.assertEqual(len(generations), 1)
        self.assertEqual(generations[0]["provider_task_id"], "seedance-task-delete")

    def test_shot_video_generation_requires_prompt_and_valid_video_config(self) -> None:
        shot = storyboard.create_storyboard_shot("project-storyboard", 1, self.payload(self.scene_a, "林晚"))
        empty_prompt = self.payload(self.scene_a, "林晚")
        empty_prompt.revision = shot["revision"]
        empty_prompt.prompt = ShotPromptPayload()
        storyboard.update_storyboard_shot("project-storyboard", 1, shot["id"], empty_prompt)

        with self.assertRaisesRegex(ValueError, "请先填写视频提示词"):
            asyncio.run(shot_videos.create_video_generation("project-storyboard", 1, shot["id"]))

        payload = self.payload(self.scene_a, "管家")
        second = storyboard.create_storyboard_shot("project-storyboard", 1, payload)
        with get_session() as session:
            config = session.get(ModelApiConfig, "video-config")
            config.last_test_status = "failed"

        with self.assertRaisesRegex(ValueError, "请先测试并通过"):
            asyncio.run(shot_videos.create_video_generation("project-storyboard", 1, second["id"]))
