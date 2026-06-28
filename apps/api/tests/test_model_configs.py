import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


os.environ["API_DATABASE_URL"] = "sqlite://"

import httpx
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.db import Base, get_engine, get_session_factory
from app.main import app
from app.services import model_configs


class _FakeAsyncClient:
    def __init__(self, response_data: dict) -> None:
        self.response_data = response_data
        self.posts: list[dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def post(self, url: str, *, json: dict, headers: dict) -> httpx.Response:
        self.posts.append({"url": url, "json": json, "headers": headers})
        request = httpx.Request("POST", url)
        return httpx.Response(200, json=self.response_data, request=request)


class ModelConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        os.environ["API_DATABASE_URL"] = f"sqlite:///{self.root}/test.db"
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        Base.metadata.create_all(bind=get_engine())
        self.client = TestClient(app)

    def tearDown(self) -> None:
        get_session_factory.cache_clear()
        get_engine.cache_clear()
        get_settings.cache_clear()
        self.temp_dir.cleanup()

    def test_create_video_model_config_uses_video_defaults(self) -> None:
        response = self.client.post(
            "/api/model-configs",
            json={
                "config_type": "video",
                "provider_name": "自定义视频模型",
                "api_base_url": "https://example.test/v1",
                "api_key": "video-secret",
                "model_name": "video-model",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["config_type"], "video")
        self.assertEqual(data["endpoint_path"], "/videos/generations")
        self.assertEqual(data["image_size"], None)
        self.assertFalse(data["supports_reference_image"])
        self.assertTrue(data["enabled"])

    def test_video_model_test_posts_to_video_generation_endpoint(self) -> None:
        created = self.client.post(
            "/api/model-configs",
            json={
                "config_type": "video",
                "provider_name": "自定义视频模型",
                "api_base_url": "https://example.test/v1",
                "api_key": "video-secret",
                "model_name": "video-model",
                "image_size": "720x1280",
                "endpoint_path": "custom/video",
            },
        ).json()
        fake_client = _FakeAsyncClient({"id": "video-test-job", "status": "queued"})

        with patch.object(model_configs.httpx, "AsyncClient", return_value=fake_client):
            response = self.client.post(f"/api/model-configs/{created['id']}/test")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(fake_client.posts[0]["url"], "https://example.test/v1/custom/video")
        self.assertEqual(fake_client.posts[0]["json"]["model"], "video-model")
        self.assertEqual(fake_client.posts[0]["json"]["size"], "720x1280")
        self.assertEqual(fake_client.posts[0]["json"]["duration"], 2)
        self.assertEqual(fake_client.posts[0]["headers"]["Authorization"], "Bearer video-secret")


if __name__ == "__main__":
    unittest.main()
