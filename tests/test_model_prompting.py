import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from litellm.types.utils import Message

from marble.llms.client_factory import get_model_name
from marble.llms.model_prompting import _log_empty_response_schema, model_prompting


class TestModelPrompting(unittest.TestCase):
    @unittest.skipUnless(os.getenv("LLM_SOURCE"), "LLM_SOURCE not set")
    def test_model_prompting(self) -> None:
        prompt = "This is a test sentence."
        message = model_prompting(
            llm_model=get_model_name(),
            messages=[{"role": "system", "content": prompt}],
            return_num=1,
            max_token_num=512,
            temperature=0.0,
            top_p=None,
            stream=None,
        )[0]
        self.assertIsInstance(message, Message)


class TestEmptyResponseLogging(unittest.TestCase):
    def test_log_empty_response_schema_writes_replayable_payload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            completion = MagicMock()
            completion.choices = [MagicMock()]
            completion.choices[0].finish_reason = "length"
            message = completion.choices[0].message
            message.role = "assistant"
            message.content = None
            message.tool_calls = []
            usage = completion.usage
            usage.completion_tokens = 8192
            usage.prompt_tokens = 723
            usage.total_tokens = 8915

            completion_kwargs = {
                "model": "openai/moonshotai/Kimi-K2.7-Code",
                "messages": [
                    {"role": "system", "content": "You are a Python developer."},
                    {"role": "user", "content": "Write code."},
                ],
                "n": 1,
                "top_p": None,
                "temperature": 0.0,
                "stream": None,
                "tools": None,
                "tool_choice": None,
                "max_completion_tokens": 8192,
                "reasoning_effort": "low",
            }

            with patch.dict(os.environ, {"MARBLE_EMPTY_RESPONSE_LOG_DIR": tmpdir}):
                _log_empty_response_schema(
                    completion_kwargs, completion, "Model returned empty response"
                )

            files = [f for f in os.listdir(tmpdir) if f.endswith(".json")]
            self.assertEqual(len(files), 1)

            with open(os.path.join(tmpdir, files[0]), "r", encoding="utf-8") as f:
                payload = json.load(f)

            self.assertEqual(payload["exception"], "Model returned empty response")
            self.assertEqual(
                payload["api_call"]["model"],
                "openai/moonshotai/Kimi-K2.7-Code",
            )
            self.assertEqual(payload["api_call"]["max_completion_tokens"], 8192)
            self.assertEqual(payload["api_call"]["reasoning_effort"], "low")
            self.assertFalse(payload["api_call"]["tools"])
            self.assertEqual(payload["response"]["finish_reason"], "length")
            self.assertEqual(payload["response"]["usage"]["completion_tokens"], 8192)
            self.assertIsNone(payload["api_call"].get("api_key"))


if __name__ == "__main__":
    unittest.main()
