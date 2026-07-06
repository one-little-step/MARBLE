import os
from typing import Optional


def get_max_token_num(preferred: Optional[int] = None, default: int = 2048) -> int:
    """
    Return the maximum output tokens to request from the LLM.

    Priority:
      1. The `preferred` argument passed by the caller.
      2. The `MAX_OUTPUT_TOKENS` environment variable.
      3. The provided `default`.

    Callers that want to opt into the centralized .env budget should pass
    ``get_max_token_num(default=<their_default>)`` as their ``max_token_num``
    argument; callers with a hard limit can pass an explicit integer directly.

    Args:
        preferred: Optional explicit value from the caller.
        default: Fallback default if nothing else is set.

    Returns:
        int: max_tokens value to pass to the LLM API.
    """
    if preferred is not None:
        return preferred
    env_value = os.environ.get("MAX_OUTPUT_TOKENS")
    if env_value:
        try:
            return int(env_value)
        except ValueError:
            pass
    return default
