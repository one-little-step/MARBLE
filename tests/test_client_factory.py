"""
Unit tests for the centralized LLM client factory.

These tests do **not** make live API calls; they only verify that the factory
resolves model names and clients correctly from the environment.
"""

import os
import unittest
from unittest import mock

from openai import OpenAI

from marble.llms.client_factory import (
    get_llm_source,
    get_model_name,
    get_openai_client,
    get_openai_credentials,
)


class TestClientFactory(unittest.TestCase):
    def test_default_source_is_openai(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_llm_source(), "openai")

    def test_source_read_from_env(self):
        with mock.patch.dict(os.environ, {"LLM_SOURCE": "rits"}, clear=True):
            self.assertEqual(get_llm_source(), "rits")

    def test_openai_model_resolution(self):
        env = {
            "LLM_SOURCE": "openai",
            "OPENAI_MODEL_NAME": "openai/deepseek-v4-flash",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(get_model_name(), "openai/deepseek-v4-flash")

    def test_rits_model_resolution(self):
        env = {
            "LLM_SOURCE": "rits",
            "RITS_MODEL_NAME": "moonshotai/Kimi-K2.7-Code",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(get_model_name(), "moonshotai/Kimi-K2.7-Code")

    def test_openai_ignores_rits_model(self):
        """When source is openai, a rits-style preferred model is ignored."""
        env = {
            "LLM_SOURCE": "openai",
            "OPENAI_MODEL_NAME": "openai/deepseek-v4-flash",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(
                get_model_name(preferred="moonshotai/Kimi-K2.7-Code"),
                "openai/deepseek-v4-flash",
            )

    def test_rits_ignores_openai_model(self):
        """When source is rits, an openai-style preferred model is ignored."""
        env = {
            "LLM_SOURCE": "rits",
            "RITS_MODEL_NAME": "moonshotai/Kimi-K2.7-Code",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(
                get_model_name(preferred="openai/deepseek-v4-flash"),
                "moonshotai/Kimi-K2.7-Code",
            )

    def test_openai_credentials(self):
        env = {
            "LLM_SOURCE": "openai",
            "OPENAI_API_KEY": "openai-key",
            "OPENAI_BASE_URL": "https://openai.example.com/v1",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            key, url = get_openai_credentials()
            self.assertEqual(key, "openai-key")
            self.assertEqual(url, "https://openai.example.com/v1")

    def test_rits_credentials_use_dummy_key(self):
        env = {
            "LLM_SOURCE": "rits",
            "RITS_API_KEY": "rits-key",
            "RITS_BASE_URL": "https://rits.example.com/v1",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            key, url = get_openai_credentials()
            self.assertEqual(key, "dummy")
            self.assertEqual(url, "https://rits.example.com/v1")

    def test_openai_client_created(self):
        env = {
            "LLM_SOURCE": "openai",
            "OPENAI_API_KEY": "openai-key",
            "OPENAI_BASE_URL": "https://openai.example.com/v1",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            client = get_openai_client()
            self.assertIsInstance(client, OpenAI)

    def test_rits_client_has_default_headers(self):
        env = {
            "LLM_SOURCE": "rits",
            "RITS_API_KEY": "rits-key",
            "RITS_BASE_URL": "https://rits.example.com/v1",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            client = get_openai_client()
            self.assertIsInstance(client, OpenAI)
            self.assertEqual(
                client.default_headers.get("RITS_API_KEY"), "rits-key"
            )

    def test_missing_required_env_raises(self):
        env = {"LLM_SOURCE": "openai"}
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError):
                get_openai_credentials()


if __name__ == "__main__":
    unittest.main()
