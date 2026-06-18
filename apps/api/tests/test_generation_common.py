import unittest
from unittest.mock import patch

import httpx

from app.services.project import generation_common


class _FakeAsyncClient:
    def __init__(self, response_data: dict) -> None:
        self.response_data = response_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def post(self, *args, **kwargs) -> httpx.Response:
        request = httpx.Request("POST", "https://example.test/chat/completions")
        return httpx.Response(200, json=self.response_data, request=request)


class TextGenerationResponseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.model_config = {
            "api_base_url": "https://example.test/v1",
            "api_key_secret": "test-key",
            "model_name": "test-model",
            "last_test_status": "success",
        }

    async def test_raw_response_preserves_plain_text_and_finish_reason(self) -> None:
        content = '第一段。\n\n她说：“别开门。”'
        client = _FakeAsyncClient(
            {"choices": [{"message": {"content": content}, "finish_reason": "stop"}]}
        )
        with (
            patch.object(generation_common.model_configs, "get_enabled_config", return_value=self.model_config),
            patch.object(generation_common.httpx, "AsyncClient", return_value=client),
        ):
            response = await generation_common.call_text_generation_raw("system", "user")

        self.assertEqual(response.content, content)
        self.assertEqual(response.finish_reason, "stop")

    async def test_structured_generation_still_parses_json(self) -> None:
        client = _FakeAsyncClient(
            {"choices": [{"message": {"content": '{"value":"改写结果"}'}, "finish_reason": "stop"}]}
        )
        with (
            patch.object(generation_common.model_configs, "get_enabled_config", return_value=self.model_config),
            patch.object(generation_common.httpx, "AsyncClient", return_value=client),
        ):
            response = await generation_common.call_text_generation_api("system", "user")

        self.assertEqual(response, {"value": "改写结果"})

    async def test_structured_generation_rejects_truncated_response(self) -> None:
        client = _FakeAsyncClient(
            {"choices": [{"message": {"content": '{"value":"未完成'}, "finish_reason": "length"}]}
        )
        with (
            patch.object(generation_common.model_configs, "get_enabled_config", return_value=self.model_config),
            patch.object(generation_common.httpx, "AsyncClient", return_value=client),
        ):
            with self.assertRaisesRegex(ValueError, "长度限制被截断"):
                await generation_common.call_text_generation_api("system", "user")


if __name__ == "__main__":
    unittest.main()
