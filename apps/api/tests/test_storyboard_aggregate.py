import os
import tempfile
import unittest
from datetime import datetime, timezone

from sqlalchemy import event


os.environ["API_DATABASE_URL"] = "sqlite://"

from app.core.config import get_settings
from app.core.db import Base, get_engine, get_session, get_session_factory
from app.models.db_models import CharacterCard, Project, ProjectCharacterSnapshot
from app.models.schemas import (
    ProjectEpisodeScriptPayload,
    ProjectStoryboardShotPayload,
    ShotPromptPayload,
    StoryboardDuplicatePayload,
    StoryboardReassignPayload,
    StoryboardReorderPayload,
)
from app.services.project.production import storyboard
from app.services.project.story import episode_scripts


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
            prompt=ShotPromptPayload(image_prompt=f"{subject}，电影感"),
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
        payload = self.payload(self.scene_a, "改写")
        payload.revision = shot["revision"] + 1
        with self.assertRaises(storyboard.StoryboardConflictError):
            storyboard.update_storyboard_shot("project-storyboard", 1, shot["id"], payload)

    def test_legacy_update_preserves_aggregate_fields(self) -> None:
        shot = storyboard.create_storyboard_shot("project-storyboard", 1, self.payload(self.scene_a, "林晚"))
        legacy = ProjectStoryboardShotPayload.model_validate({
            "shot_no": 1, "scene": "客厅近景", "visual_prompt": "低照度客厅",
            "duration_seconds": 4, "status": "draft",
        })
        updated = storyboard.update_storyboard_shot("project-storyboard", 1, shot["id"], legacy)
        self.assertEqual(updated["source_scene_id"], self.scene_a)
        self.assertEqual(updated["subject_description"], "林晚")
        self.assertEqual(updated["prompt"]["image_prompt"], "低照度客厅")
