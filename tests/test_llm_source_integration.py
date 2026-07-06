"""
Integration tests that exercise real LLM calls.

These tests are skipped unless the corresponding source is selected via
``LLM_SOURCE`` in the environment and credentials are present.

Run with OpenAI source:
    LLM_SOURCE=openai python -m unittest tests.test_llm_source_integration -v

Run with RITS source:
    LLM_SOURCE=rits python -m unittest tests.test_llm_source_integration -v
"""

import os
import unittest

from marble.llms.client_factory import get_llm_source, get_model_name
from marble.llms.model_prompting import model_prompting


@unittest.skipUnless(os.getenv("LLM_SOURCE"), "LLM_SOURCE not set")
class TestLLMSourceIntegration(unittest.TestCase):
    def test_model_prompting_returns_non_empty(self):
        """A simple real call through model_prompting must return content."""
        model = get_model_name()
        result = model_prompting(
            llm_model=model,
            messages=[{"role": "user", "content": "Say exactly 'hello' and nothing else."}],
            max_token_num=64,
            temperature=0.0,
        )
        self.assertEqual(len(result), 1)
        message = result[0]
        self.assertTrue(
            message.content,
            f"Model {model} returned empty content for source={get_llm_source()}",
        )
        self.assertIn("hello", message.content.lower())

    def test_model_name_matches_source(self):
        """The resolved model name must match the active source family."""
        source = get_llm_source()
        model = get_model_name()
        if source == "rits":
            self.assertTrue(
                model.startswith("moonshotai/") or model.startswith("ibm/"),
                f"RITS source should use a RITS model, got {model}",
            )
        else:
            self.assertTrue(
                model.startswith("openai/")
                or model.startswith("gpt-")
                or model.startswith("deepseek"),
                f"OpenAI source should use an OpenAI-compatible model, got {model}",
            )


if __name__ == "__main__":
    unittest.main()
