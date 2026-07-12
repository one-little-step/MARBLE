import os

import litellm
from beartype import beartype
from beartype.typing import List, Optional

from .error_handler import api_calling_error_exponential_backoff


def _normalize_ollama_model(model: str, api_base: Optional[str]) -> str:
    """
    LiteLLM requires a provider prefix (e.g. 'ollama/embeddinggemma').
    When a custom local endpoint is configured and the model has no prefix,
    default to the Ollama provider.
    """
    if "/" in model:
        return model
    if api_base and ("localhost:11434" in api_base or "127.0.0.1:11434" in api_base):
        return f"ollama/{model}"
    return model


def get_embedding_config(model: Optional[str] = None) -> tuple[str, Optional[str]]:
    """
    Resolve embedding model and endpoint.

    Environment variables take precedence when set:
      - EMBEDDING_MODEL: model name passed to litellm.embedding
      - EMBEDDING_URL: custom api_base for the embedding endpoint

    Args:
        model: Fallback model name if EMBEDDING_MODEL is not set.

    Returns:
        Tuple of (resolved_model, api_base_or_none).
    """
    api_base = os.environ.get("EMBEDDING_URL") or None
    resolved_model = os.environ.get("EMBEDDING_MODEL", model or "text-embedding-3-small")
    resolved_model = _normalize_ollama_model(resolved_model, api_base)
    return resolved_model, api_base


@beartype
@api_calling_error_exponential_backoff(retries=5, base_wait_time=1)
def text_embedding(
    model: str,
    input: str,
) -> List[float]:
    """
    Select model via router in LiteLLM with support for function calling.
    """
    resolved_model, api_base = get_embedding_config(model)
    kwargs: dict = {"model": resolved_model, "input": [input]}
    if api_base is not None:
        kwargs["api_base"] = api_base
    # litellm.set_verbose=True
    embedding = litellm.embedding(**kwargs)
    embedding_0 = embedding.data[0]["embedding"]
    assert embedding_0 is not None
    assert isinstance(embedding_0, list)
    return embedding_0
