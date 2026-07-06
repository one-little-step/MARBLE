import datetime
import json
import logging
import os

import litellm
from beartype import beartype
from beartype.typing import Any, Dict, List, Optional
from litellm.types.utils import Message

from marble.llms.client_factory import (
    _require_env,
    get_llm_source,
    get_model_name,
)
from marble.llms.error_handler import api_calling_error_exponential_backoff
from marble.llms.token_config import get_max_token_num, get_reasoning_effort

logger = logging.getLogger(__name__)


def _resolve_litellm_model(preferred_model: Optional[str] = None) -> str:
    """
    Resolve the model string to pass to LiteLLM.

    For the ``openai`` source we use the model name as configured (it already
    carries the ``openai/`` provider prefix expected by LiteLLM).

    For the ``rits`` source we prefix the model with ``openai/`` so LiteLLM
    routes through an OpenAI-compatible client.
    """
    source = get_llm_source()
    model = get_model_name(preferred=preferred_model)

    if source == "rits":
        # LiteLLM needs a provider prefix; RITS is OpenAI-compatible.
        if not model.startswith("openai/"):
            model = f"openai/{model}"
    return model


def _resolve_litellm_credentials() -> tuple[str, str, Optional[Dict[str, str]]]:
    """
    Return (api_key, base_url, extra_headers) for the active LLM source.

    For RITS, the OpenAI-compatible endpoint expects the real key in the
    ``RITS_API_KEY`` header and a non-empty placeholder for the standard
    ``api_key`` field.
    """
    source = get_llm_source()

    if source == "rits":
        return (
            "dummy",
            _require_env("RITS_BASE_URL"),
            {
                "RITS_API_KEY": _require_env("RITS_API_KEY"),
                "accept": "application/json",
            },
        )

    return _require_env("OPENAI_API_KEY"), _require_env("OPENAI_BASE_URL"), None


def _log_empty_response_schema(
    completion_kwargs: Dict[str, Any],
    completion: Any,
    exception_message: str,
) -> None:
    """
    Persist the exact API call schema and response metadata when a model returns
    an empty response so the failing call can be replayed in isolation.
    """
    debug_dir = os.environ.get(
        "MARBLE_EMPTY_RESPONSE_LOG_DIR", "outputs/debug/empty_responses"
    )
    try:
        os.makedirs(debug_dir, exist_ok=True)
    except OSError:
        logger.exception("Failed to create empty-response debug directory")
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    model_slug = str(completion_kwargs.get("model", "unknown")).replace("/", "_")
    file_path = os.path.join(debug_dir, f"empty_response_{timestamp}_{model_slug}.json")

    choice = completion.choices[0] if completion and completion.choices else None
    message = choice.message if choice else None
    payload = {
        "timestamp": timestamp,
        "exception": exception_message,
        "source": get_llm_source(),
        "api_call": {
            # Strip credentials before persisting.
            "model": completion_kwargs.get("model"),
            "messages": completion_kwargs.get("messages"),
            "n": completion_kwargs.get("n"),
            "top_p": completion_kwargs.get("top_p"),
            "temperature": completion_kwargs.get("temperature"),
            "stream": completion_kwargs.get("stream"),
            "tools": bool(completion_kwargs.get("tools")),
            "tool_choice": completion_kwargs.get("tool_choice"),
            "max_tokens": completion_kwargs.get("max_tokens"),
            "max_completion_tokens": completion_kwargs.get("max_completion_tokens"),
            "reasoning_effort": completion_kwargs.get("reasoning_effort"),
        },
        "response": {
            "finish_reason": getattr(choice, "finish_reason", None),
            "role": getattr(message, "role", None),
            "content": getattr(message, "content", None),
            "tool_calls": [
                {
                    "id": getattr(tc, "id", None),
                    "type": getattr(tc, "type", None),
                    "function": {
                        "name": getattr(getattr(tc, "function", None), "name", None),
                        "arguments": getattr(getattr(tc, "function", None), "arguments", None),
                    },
                }
                for tc in (getattr(message, "tool_calls", []) or [])
            ],
            "usage": _usage_to_dict(completion),
        },
    }

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False, default=str)
        logger.info("Empty response schema logged to %s", file_path)
    except Exception:
        logger.exception("Failed to write empty-response debug payload")


def _usage_to_dict(completion: Any) -> Optional[Dict[str, Any]]:
    usage = getattr(completion, "usage", None)
    if usage is None:
        return None
    return {
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
    }


def _model_prompting_inner(
    llm_model: str,
    messages: List[Dict[str, str]],
    return_num: Optional[int] = 1,
    max_token_num: Optional[int] = 2048,
    temperature: Optional[float] = 0.0,
    top_p: Optional[float] = None,
    stream: Optional[bool] = None,
    mode: Optional[str] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
) -> Optional[List[Message]]:
    """
    Select model via router in LiteLLM with support for function calling.
    """
    max_token_num = get_max_token_num(preferred=max_token_num)
    reasoning_effort = get_reasoning_effort(preferred=reasoning_effort)

    model = _resolve_litellm_model(preferred_model=llm_model)
    api_key, base_url, extra_headers = _resolve_litellm_credentials()

    if "together_ai/TA" in llm_model:
        base_url = "https://api.ohmygpt.com/v1"
        extra_headers = None

    source = get_llm_source()
    token_param = "max_completion_tokens" if source == "rits" else "max_tokens"
    logger.info(
        f"LiteLLM call: source={source}, model={model}, "
        f"base_url={base_url}, api_key={'SET' if api_key else 'NOT SET'}, "
        f"{token_param}={max_token_num}, reasoning_effort={reasoning_effort}, "
        f"tools={'YES' if tools else 'NO'}"
    )

    completion_kwargs: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "n": return_num,
        "top_p": top_p,
        "temperature": temperature,
        "stream": stream,
        "tools": tools,
        "tool_choice": tool_choice,
        "api_key": api_key,
        "base_url": base_url,
        "drop_params": True,  # Silently drop unsupported params (e.g. thinking)
    }

    # RITS (Kimi/K2) returns empty responses when ``max_tokens`` is used;
    # it expects ``max_completion_tokens`` instead. Other OpenAI-compatible
    # providers still use ``max_tokens``.
    if source == "rits":
        completion_kwargs["max_completion_tokens"] = max_token_num
        # Reasoning-effort is supported by some reasoning models. If the
        # provider does not recognize it, ``drop_params=True`` removes it.
        if reasoning_effort:
            completion_kwargs["reasoning_effort"] = reasoning_effort
    else:
        completion_kwargs["max_tokens"] = max_token_num

    if extra_headers:
        completion_kwargs["extra_headers"] = extra_headers

    completion = litellm.completion(**completion_kwargs)
    message_0: Message = completion.choices[0].message
    usage = getattr(completion, "usage", None)
    logger.debug(
        f"LiteLLM response: content={repr(message_0.content)[:200]}, "
        f"tool_calls={message_0.tool_calls}, role={message_0.role}, usage={usage}"
    )
    if message_0 is None or (not message_0.content and not message_0.tool_calls):
        exc_msg = "Model returned empty response (likely used all tokens for reasoning)"
        _log_empty_response_schema(completion_kwargs, completion, exc_msg)
        raise ValueError(exc_msg)
    assert isinstance(message_0, Message)
    return [message_0]


@api_calling_error_exponential_backoff(retries=5, base_wait_time=1)
def _model_prompting_with_retry(**kwargs: Any) -> Optional[List[Message]]:
    return _model_prompting_inner(**kwargs)


def model_prompting(
    llm_model: str,
    messages: List[Dict[str, str]],
    return_num: Optional[int] = 1,
    max_token_num: Optional[int] = 2048,
    temperature: Optional[float] = 0.0,
    top_p: Optional[float] = None,
    stream: Optional[bool] = None,
    mode: Optional[str] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
) -> List[Message]:
    result = _model_prompting_with_retry(
        llm_model=llm_model,
        messages=messages,
        return_num=return_num,
        max_token_num=max_token_num,
        temperature=temperature,
        top_p=top_p,
        stream=stream,
        mode=mode,
        tools=tools,
        tool_choice=tool_choice,
        reasoning_effort=reasoning_effort,
    )
    if result is None:
        logger.warning("model_prompting returned None after all retries, returning fallback message")
        return [Message(content="[Error: Model failed to generate a response after multiple retries]", role="assistant")]
    return result
