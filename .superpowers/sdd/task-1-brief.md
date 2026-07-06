### Task 1: Add centralized max-token configuration

**Files:**
- Create: `marble/llms/token_config.py`
- Modify: `.env`
- Modify: `marble/llms/model_prompting.py`
- Test: `tests/test_token_config.py`

**Interfaces:**
- Consumes: `os.environ`, `LLM_SOURCE` from `.env`
- Produces: `get_max_token_num(preferred: Optional[int] = None) -> int`

- [ ] **Step 1: Write the env-driven token helper**

Create `marble/llms/token_config.py`:

```python
import os
from typing import Optional


def get_max_token_num(preferred: Optional[int] = None, default: int = 2048) -> int:
    """
    Return the maximum output tokens to request from the LLM.

    Priority:
      1. The `preferred` argument passed by the caller.
      2. The `MAX_OUTPUT_TOKENS` environment variable.
      3. The provided `default`.

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
```

- [ ] **Step 2: Wire helper into `model_prompting.py`**

Modify `marble/llms/model_prompting.py`:

```python
from marble.llms.token_config import get_max_token_num
```

Update both `_model_prompting_inner` signatures and the `max_tokens` assignment so that:

```python
max_token_num = get_max_token_num(preferred=max_token_num)
```

is used before building the LiteLLM kwargs in both the tool and non-tool paths.

- [ ] **Step 3: Add `MAX_OUTPUT_TOKENS` to `.env`**

Append to `.env`:

```bash
# ---------------------------------------------------------------------------
# Global token budget
# ---------------------------------------------------------------------------
MAX_OUTPUT_TOKENS=8192
```

- [ ] **Step 4: Write unit tests**

Create `tests/test_token_config.py`:

```python
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
```

- [ ] **Step 5: Run tests**

Run:

```bash
source venv/bin/activate
python -m pytest tests/test_token_config.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add marble/llms/token_config.py marble/llms/model_prompting.py .env tests/test_token_config.py
git commit -m "feat: centralize max output tokens via MAX_OUTPUT_TOKENS env var"
```

---

