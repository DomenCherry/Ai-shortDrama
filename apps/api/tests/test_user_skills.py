import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch


os.environ["API_DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.db import Base, get_engine, get_session_factory
from app.main import app
from app.models.schemas import EpisodeContentGenerationCreate, UserSkillUpdate
from app.services import user_skills
from app.services.project.story import episode_contents


class UserSkillTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.skills_dir = self.root / "skills"
        self.skill_dir = self.skills_dir / "short-drama-creator"
        self.skill_dir.mkdir(parents=True)
        (self.skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: short-drama-creator\n"
            "description: 当需要帮助用户创建 AI 短剧项目时使用。\n"
            "---\n\n"
            "# 短剧创作辅助\n",
            encoding="utf-8",
        )

        os.environ["API_DATABASE_URL"] = f"sqlite:///{self.root}/test.db"
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        Base.metadata.create_all(bind=get_engine())
        self.skills_root_patch = patch.object(user_skills, "skills_root", return_value=self.skills_dir)
        self.skills_root_patch.start()

    def tearDown(self) -> None:
        self.skills_root_patch.stop()
        get_session_factory.cache_clear()
        get_engine.cache_clear()
        get_settings.cache_clear()
        self.temp_dir.cleanup()

    def test_list_api_discovers_user_skill_enabled_by_default(self) -> None:
        response = TestClient(app).get("/api/skills")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "name": "short-drama-creator",
                    "description": "当需要帮助用户创建 AI 短剧项目时使用。",
                    "source_dir": "skills/short-drama-creator",
                    "enabled": True,
                    "updated_at": None,
                }
            ],
        )

    def test_update_api_persists_skill_enabled_state(self) -> None:
        client = TestClient(app)

        disabled = client.patch("/api/skills/short-drama-creator", json={"enabled": False})
        listed = client.get("/api/skills")

        self.assertEqual(disabled.status_code, 200)
        self.assertFalse(disabled.json()["enabled"])
        self.assertFalse(listed.json()[0]["enabled"])
        self.assertIsNotNone(listed.json()[0]["updated_at"])

    async def test_disabled_skill_blocks_generation_before_model_call(self) -> None:
        user_skills.update_user_skill("short-drama-creator", UserSkillUpdate(enabled=False))
        model_call = AsyncMock()

        with patch.object(episode_contents, "call_text_generation_raw", new=model_call):
            with self.assertRaisesRegex(ValueError, "short-drama-creator skill 已禁用"):
                await episode_contents.generate_episode_content(
                    "missing-project",
                    1,
                    EpisodeContentGenerationCreate(client_request_id="blocked"),
                )

        model_call.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
