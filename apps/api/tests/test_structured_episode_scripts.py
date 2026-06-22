import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from sqlalchemy import event


os.environ["API_DATABASE_URL"] = "sqlite://"

from app.core.config import get_settings
from app.core.db import Base, get_engine, get_session, get_session_factory
from app.models.db_models import (
    CharacterCard,
    Project,
    ProjectCharacterSnapshot,
    ProjectCopywriting,
    ProjectEpisodeContent,
    ProjectStoryboardShot,
)
from app.models.schemas import (
    ProjectEpisodeScriptResponse,
    ScriptGenerationAdoptResponse,
    ProjectEpisodeScriptPayload,
    ScriptGenerationCreate,
    ScriptRevisionPayload,
)
from app.services.project.story import episode_scripts


class StructuredEpisodeScriptTests(unittest.IsolatedAsyncioTestCase):
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
        self.project_id = "project-structured"
        self.character_id = "character-snapshot-1"
        self._seed()

    def tearDown(self) -> None:
        get_session_factory.cache_clear()
        get_engine.cache_clear()
        get_settings.cache_clear()
        self.temp_dir.cleanup()

    def _seed(self) -> None:
        now = datetime.now(timezone.utc)
        with get_session() as session:
            session.add(Project(
                id=self.project_id, title="结构化剧本测试", idea="复仇短剧", episode_count=2,
                episode_duration=1, total_duration=2, status="draft", created_at=now, updated_at=now,
            ))
            session.add(ProjectEpisodeContent(
                id="content-1", project_id=self.project_id, episode_no=1,
                detailed_content="林晚推门而入，发现遗嘱已经被调换。",
                word_count=18, status="confirmed", created_at=now, updated_at=now,
            ))
            session.add(CharacterCard(
                id="source-card-1", name="林晚", gender="女", role_type="主角",
                identity="调查记者", goal="找回遗嘱", status="active",
                created_at=now, updated_at=now,
            ))
            session.add(ProjectCharacterSnapshot(
                id=self.character_id, project_id=self.project_id, source_character_card_id="source-card-1",
                source_version=1, name="林晚", gender="女", role_type="主角", snapshot_content="{}",
                loaded_at=now, updated_at=now,
            ))
            session.add(ProjectStoryboardShot(
                id="shot-1", project_id=self.project_id, episode_no=1, shot_no=1,
                status="confirmed", created_at=now, updated_at=now,
            ))
            session.add(ProjectCopywriting(
                id="copy-1", project_id=self.project_id, episode_no=1,
                status="confirmed", created_at=now, updated_at=now,
            ))

    def _payload(self, revision=None, content="你终于来了。", title="遗嘱之夜") -> ProjectEpisodeScriptPayload:
        return ProjectEpisodeScriptPayload.model_validate({
            "revision": revision,
            "title": title,
            "scenes": [{
                "title": "对峙",
                "location": "林家客厅",
                "time_of_day": "night",
                "interior_exterior": "interior",
                "character_snapshot_ids": [self.character_id],
                "story_purpose": "揭示遗嘱被调换",
                "blocks": [
                    {"block_type": "action", "content": "林晚推门而入。"},
                    {"block_type": "dialogue", "character_snapshot_id": self.character_id, "content": content},
                ],
            }],
        })

    def test_atomic_save_preserves_ids_versions_and_marks_downstream(self) -> None:
        created = episode_scripts.upsert_episode_script(self.project_id, 1, self._payload())
        self.assertEqual(created["revision"], 1)
        self.assertEqual(created["version"], 1)
        self.assertEqual(len(created["scenes"]), 1)
        self.assertGreater(created["auto_duration_seconds"], 0)
        scene_id = created["scenes"][0]["id"]
        block_ids = [item["id"] for item in created["scenes"][0]["blocks"]]

        title_only = self._payload(created["revision"], title="新的展示标题")
        title_only.scenes[0].id = scene_id
        for block, block_id in zip(title_only.scenes[0].blocks, block_ids):
            block.id = block_id
        updated = episode_scripts.upsert_episode_script(self.project_id, 1, title_only)
        self.assertEqual(updated["revision"], 2)
        self.assertEqual(updated["version"], 1)
        self.assertEqual(updated["scenes"][0]["id"], scene_id)

        substantive = self._payload(updated["revision"], content="你来晚了。", title="新的展示标题")
        substantive.scenes[0].id = scene_id
        for block, block_id in zip(substantive.scenes[0].blocks, block_ids):
            block.id = block_id
        changed = episode_scripts.upsert_episode_script(self.project_id, 1, substantive)
        self.assertEqual(changed["version"], 2)
        with get_session() as session:
            self.assertEqual(session.get(ProjectStoryboardShot, "shot-1").status, "needs_review")
            self.assertEqual(session.get(ProjectCopywriting, "copy-1").status, "needs_review")

    def test_revision_conflict_does_not_overwrite(self) -> None:
        created = episode_scripts.upsert_episode_script(self.project_id, 1, self._payload())
        with self.assertRaises(episode_scripts.ScriptConflictError):
            episode_scripts.upsert_episode_script(self.project_id, 1, self._payload(revision=created["revision"] + 1))
        current = episode_scripts.get_episode_script(self.project_id, 1)
        self.assertEqual(current["revision"], created["revision"])

    def test_draft_can_be_incomplete_but_confirmation_is_blocked(self) -> None:
        incomplete = episode_scripts.upsert_episode_script(self.project_id, 1, ProjectEpisodeScriptPayload(
            revision=None,
            scenes=[{"location": None, "blocks": [{"block_type": "dialogue", "content": "无人说话"}]}],
        ))
        self.assertTrue(any(issue["severity"] == "error" for issue in incomplete["validation_issues"]))
        with self.assertRaises(episode_scripts.ScriptValidationError):
            episode_scripts.confirm_episode_script(self.project_id, 1, ScriptRevisionPayload(revision=incomplete["revision"]))

    def test_confirmed_script_returns_to_draft_after_substantive_edit(self) -> None:
        created = episode_scripts.upsert_episode_script(self.project_id, 1, self._payload())
        confirmed = episode_scripts.confirm_episode_script(self.project_id, 1, ScriptRevisionPayload(revision=created["revision"]))
        self.assertEqual(confirmed["status"], "confirmed")
        payload = self._payload(confirmed["revision"], content="遗嘱已经生效。")
        payload.scenes[0].id = confirmed["scenes"][0]["id"]
        for block, current in zip(payload.scenes[0].blocks, confirmed["scenes"][0]["blocks"]):
            block.id = current["id"]
        changed = episode_scripts.upsert_episode_script(self.project_id, 1, payload)
        self.assertEqual(changed["status"], "draft")

    async def test_episode_generation_is_candidate_until_adopted(self) -> None:
        output = {
            "title": "遗嘱之夜",
            "scenes": [{
                "title": "对峙", "location": "林家客厅", "time_of_day": "night",
                "interior_exterior": "interior", "character_snapshot_ids": [self.character_id],
                "blocks": [{"block_type": "action", "content": "林晚推门而入。"}],
            }],
        }
        request = ScriptGenerationCreate(
            generation_scope="episode", target_block_ids=[], client_request_id="request-1",
            base_script_version=None, base_script_revision=None,
        )
        model_config = {"id": "model-1", "model_name": "test", "last_test_status": "success"}
        with (
            patch.object(episode_scripts.model_configs, "get_enabled_config", return_value=model_config),
            patch.object(episode_scripts, "call_text_generation_api", new=AsyncMock(return_value=output)),
        ):
            generation = await episode_scripts.generate_episode_script(self.project_id, 1, request)
        self.assertEqual(generation["status"], "candidate")
        self.assertIsNone(episode_scripts.get_episode_script(self.project_id, 1))
        adopted = episode_scripts.adopt_script_generation(
            self.project_id, 1, generation["id"], ScriptRevisionPayload(revision=None)
        )
        self.assertEqual(adopted["generation"]["status"], "adopted")
        self.assertEqual(adopted["script"]["version"], 1)
        self.assertEqual(adopted["script"]["scenes"][0]["location"], "林家客厅")
        ProjectEpisodeScriptResponse.model_validate(adopted["script"])
        ScriptGenerationAdoptResponse.model_validate(adopted)


if __name__ == "__main__":
    unittest.main()
