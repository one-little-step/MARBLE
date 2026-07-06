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
from marble.llms.token_config import get_max_token_num

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
) -> Optional[List[Message]]:
    """
    Select model via router in LiteLLM with support for function calling.
    """
    max_token_num = get_max_token_num(preferred=max_token_num)

    model = _resolve_litellm_model(preferred_model=llm_model)
    api_key, base_url, extra_headers = _resolve_litellm_credentials()

    if "together_ai/TA" in llm_model:
        base_url = "https://api.ohmygpt.com/v1"
        extra_headers = None

    logger.info(
        f"LiteLLM call: source={get_llm_source()}, model={model}, "
        f"base_url={base_url}, api_key={'SET' if api_key else 'NOT SET'}, "
        f"max_tokens={max_token_num}, tools={'YES' if tools else 'NO'}"
    )

    completion_kwargs: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_token_num,
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

    if extra_headers:
        completion_kwargs["extra_headers"] = extra_headers

    completion = litellm.completion(**completion_kwargs)
    message_0: Message = completion.choices[0].message
    if message_0 is None or (not message_0.content and not message_0.tool_calls):
        raise ValueError("Model returned empty response (likely used all tokens for reasoning)")
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
    )
    if result is None:
        logger.warning("model_prompting returned None after all retries, returning fallback message")
        return [Message(content="[Error: Model failed to generate a response after multiple retries]", role="assistant")]
    return result
