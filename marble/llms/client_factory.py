"""
Centralized LLM client/model configuration resolver.

Set ``LLM_SOURCE=openai`` or ``LLM_SOURCE=rits`` in the environment (or .env)
to control every LLM call in MARBLE.

Examples
--------
>>> from marble.llms.client_factory import get_openai_client, get_model_name
>>> client = get_openai_client()
>>> model = get_model_name()
"""

import os
from typing import Optional

from openai import OpenAI


def get_llm_source() -> str:
    """Return the active LLM source, lower-cased. Defaults to ``openai``."""
    return os.getenv("LLM_SOURCE", "openai").strip().lower()


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable '{name}' for LLM_SOURCE={get_llm_source()}. "
            f"Please check your .env file."
        )
    return value


def get_model_name(preferred: Optional[str] = None) -> str:
    """
    Resolve the model name for the active ``LLM_SOURCE``.

    ``LLM_SOURCE`` is the single switch that controls the flow. The optional
    *preferred* value is honored only when it looks like an explicit user choice
    for the active source (e.g. a RITS-style model name when source is ``rits``,
    or an ``openai/`` prefixed model when source is ``openai``). Otherwise the
    model named in the environment for the active source wins.
    """
    source = get_llm_source()

    if preferred:
        preferred_norm = preferred.strip()
        is_rits_model = preferred_norm.startswith("moonshotai/") or preferred_norm.startswith("ibm/")
        is_openai_model = preferred_norm.startswith("openai/") or preferred_norm in (
            "gpt-3.5-turbo",
            "gpt-4o",
            "deepseek-v4-flash",
        )

        if source == "rits" and is_rits_model:
            return preferred_norm
        if source == "openai" and is_openai_model:
            return preferred_norm

    if source == "rits":
        return os.getenv("RITS_MODEL_NAME", "moonshotai/Kimi-K2.7-Code")

    return os.getenv("OPENAI_MODEL_NAME", "openai/deepseek-v4-flash")


def get_openai_credentials() -> tuple[str, str]:
    """
    Return (api_key, base_url) for the active LLM source.

    For RITS, the OpenAI SDK requires a non-empty ``api_key`` argument, so we
    return a dummy value; the real authentication is sent via the
    ``RITS_API_KEY`` header.
    """
    source = get_llm_source()

    if source == "rits":
        return (
            "dummy",  # OpenAI SDK placeholder
            _require_env("RITS_BASE_URL"),
        )

    return _require_env("OPENAI_API_KEY"), _require_env("OPENAI_BASE_URL")


def get_openai_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: Optional[float] = None,
) -> OpenAI:
    """
    Create an :class:`openai.OpenAI` client for the active LLM source.

    Any explicit ``api_key``/``base_url`` overrides the environment defaults.
    """
    source = get_llm_source()
    key, url = get_openai_credentials()

    if api_key is not None:
        key = api_key
    if base_url is not None:
        url = base_url

    client_kwargs: dict = {"api_key": key, "base_url": url}

    if timeout is not None:
        client_kwargs["timeout"] = timeout

    if source == "rits":
        client_kwargs["default_headers"] = {
            "RITS_API_KEY": _require_env("RITS_API_KEY"),
            "accept": "application/json",
        }

    return OpenAI(**client_kwargs)


def get_default_timeout() -> float:
    """Default HTTP timeout for direct OpenAI clients."""
    return float(os.getenv("LLM_TIMEOUT", "120"))
