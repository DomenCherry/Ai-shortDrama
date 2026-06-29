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
    def __init__(self, response_data: dict, status_code: int = 200) -> None:
        self.response_data = response_data
        self.status_code = status_code
        self.posts: list[dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def post(self, url: str, *, json: dict, headers: dict) -> httpx.Response:
        self.posts.append({"url": url, "json": json, "headers": headers})
        request = httpx.Request("POST", url)
        return httpx.Response(self.status_code, json=self.response_data, request=request)


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

    def test_create_video_model_config_uses_video_endpoint(self) -> None:
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
        self.assertNotIn("video_defaults", data)
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
        self.assertEqual(fake_client.posts[0]["json"]["size"], "1280x720")
        self.assertEqual(fake_client.posts[0]["json"]["duration"], 2)
        self.assertEqual(fake_client.posts[0]["headers"]["Authorization"], "Bearer video-secret")

    def test_create_seedance_video_preset_stores_connection_fields(self) -> None:
        response = self.client.post(
            "/api/model-configs",
            json={
                "config_type": "video",
                "provider_mode": "preset",
                "provider_preset": "volcengine_seedance_1_5",
                "api_key": "video-secret",
                "model_name": "doubao-seedance-1-5-Pro-251215",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["provider_mode"], "preset")
        self.assertEqual(data["provider_preset"], "volcengine_seedance_1_5")
        self.assertEqual(data["provider_name"], "火山方舟")
        self.assertEqual(data["api_base_url"], "https://ark.cn-beijing.volces.com/api/v3")
        self.assertEqual(data["endpoint_path"], "/contents/generations/tasks")
        self.assertNotIn("video_defaults", data)

    def test_update_seedance_video_preset_keeps_endpoint_and_model_name_is_editable(self) -> None:
        created = self.client.post(
            "/api/model-configs",
            json={
                "config_type": "video",
                "provider_mode": "preset",
                "provider_preset": "volcengine_seedance_1_5",
                "api_key": "video-secret",
                "model_name": "doubao-seedance-1-5-Pro-251215",
            },
        ).json()

        response = self.client.put(
            f"/api/model-configs/{created['id']}",
            json={
                "provider_mode": "preset",
                "provider_preset": "volcengine_seedance_1_5",
                "provider_name": "should be ignored",
                "api_base_url": "https://wrong.example",
                "model_name": "custom-endpoint-id",
                "endpoint_path": "/wrong",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["model_name"], "custom-endpoint-id")
        self.assertEqual(data["api_base_url"], "https://ark.cn-beijing.volces.com/api/v3")
        self.assertEqual(data["endpoint_path"], "/contents/generations/tasks")
        self.assertNotIn("video_defaults", data)

    def test_seedance_video_model_test_posts_to_task_endpoint(self) -> None:
        created = self.client.post(
            "/api/model-configs",
            json={
                "config_type": "video",
                "provider_mode": "preset",
                "provider_preset": "volcengine_seedance_1_5",
                "api_key": "video-secret",
                "model_name": "doubao-seedance-1-5-Pro-251215",
            },
        ).json()
        fake_client = _FakeAsyncClient({"id": "seedance-test-task"})

        with patch.object(model_configs.httpx, "AsyncClient", return_value=fake_client):
            response = self.client.post(f"/api/model-configs/{created['id']}/test")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        request = fake_client.posts[0]
        self.assertEqual(request["url"], "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks")
        self.assertEqual(request["json"]["model"], "doubao-seedance-1-5-Pro-251215")
        self.assertEqual(request["json"]["content"][0]["type"], "text")
        self.assertEqual(request["json"]["resolution"], "480p")
        self.assertEqual(request["json"]["ratio"], "16:9")
        self.assertEqual(request["json"]["duration"], 4)
        self.assertFalse(request["json"]["generate_audio"])
        self.assertFalse(request["json"]["watermark"])
        self.assertFalse(request["json"]["camera_fixed"])
        self.assertTrue(request["json"]["draft"])
        self.assertEqual(request["headers"]["Authorization"], "Bearer video-secret")

    def test_seedance_video_model_test_404_includes_provider_detail(self) -> None:
        created = self.client.post(
            "/api/model-configs",
            json={
                "config_type": "video",
                "provider_mode": "preset",
                "provider_preset": "volcengine_seedance_1_5",
                "api_key": "video-secret",
                "model_name": "doubao-seedance-1-5-Pro-251215",
            },
        ).json()
        fake_client = _FakeAsyncClient(
            {"error": {"message": "The model does not exist."}, "code": "ModelNotFound"},
            status_code=404,
        )

        with patch.object(model_configs.httpx, "AsyncClient", return_value=fake_client):
            response = self.client.post(f"/api/model-configs/{created['id']}/test")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("接口返回错误状态：404", data["message"])
        self.assertIn("The model does not exist.", data["message"])
        self.assertIn("Endpoint ID", data["message"])

if __name__ == "__main__":
    unittest.main()
