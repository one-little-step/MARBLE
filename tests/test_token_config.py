import os
import pytest

from marble.llms.token_config import get_max_token_num


class TestGetMaxTokenNum:
    def test_preferred_wins(self, monkeypatch):
        monkeypatch.setenv("MAX_OUTPUT_TOKENS", "1000")
        assert get_max_token_num(preferred=2048) == 2048

    def test_env_used_when_no_preferred(self, monkeypatch):
        monkeypatch.setenv("MAX_OUTPUT_TOKENS", "4096")
        assert get_max_token_num() == 4096

    def test_default_used_when_env_missing(self, monkeypatch):
        monkeypatch.delenv("MAX_OUTPUT_TOKENS", raising=False)
        assert get_max_token_num() == 2048

    def test_default_override(self, monkeypatch):
        monkeypatch.delenv("MAX_OUTPUT_TOKENS", raising=False)
        assert get_max_token_num(default=1024) == 1024

    def test_invalid_env_ignored(self, monkeypatch):
        monkeypatch.setenv("MAX_OUTPUT_TOKENS", "not_a_number")
        assert get_max_token_num() == 2048
