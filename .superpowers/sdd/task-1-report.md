# Task 1 Report: Centralized max-token configuration

## Status

DONE

## Summary

Created `marble/llms/token_config.py` with a `get_max_token_num` helper that resolves max output tokens in priority order: explicit caller preference, `MAX_OUTPUT_TOKENS` environment variable, then a fallback default. Wired the helper into `marble/llms/model_prompting.py` by importing it and applying `max_token_num = get_max_token_num(preferred=max_token_num)` before the LiteLLM kwargs are built, so both tool and non-tool paths use the centralized configuration. Added `MAX_OUTPUT_TOKENS=8192` to `.env` (force-added because `.env` is gitignored). Wrote unit tests in `tests/test_token_config.py` covering preference precedence, env usage, default fallback, default override, and invalid env values.

Pytest was not installed in the project venv, so I installed it as a one-time environment preparation step before running tests.

## Test Commands and Output

```bash
source venv/bin/activate
python -m pytest tests/test_token_config.py -v
```

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, plugelliptic 1.6.0 -- /Users/saptarshi/workfiles/MARBLE/MARBLE/venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/saptarshi/workfiles/MARBLE/MARBLE
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 5 items

tests/test_token_config.py::TestGetMaxTokenNum::test_preferred_wins PASSED [ 20%]
tests/test_token_config.py::TestGetMaxTokenNum::test_env_used_when_no_preferred PASSED [ 40%]
tests/test_token_config.py::TestGetMaxTokenNum::test_default_used_when_env_missing PASSED [ 60%]
tests/test_token_config.py::TestGetMaxTokenNum::test_default_override PASSED [ 80%]
tests/test_token_config.py::TestGetMaxTokenNum::test_invalid_env_ignored PASSED [100%]

============================== 5 passed in 1.63s ===============================
```

Additional regression test:

```bash
source venv/bin/activate
python -m pytest tests/test_model_prompting.py -v
```

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Users/saptarshi/workfiles/MARBLE/MARBLE/venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/saptarshi/workfiles/MARBLE/MARBLE
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 1 item

tests/test_model_prompting.py::TestModelPrompting::test_model_prompting PASSED [100%]

============================== 1 passed in 6.01s ===============================
```

## Commit

- **Hash:** `a6b1b94`
- **Message:** `feat: centralize max output tokens via MAX_OUTPUT_TOKENS env var`

## Concerns / Blockers

- `.env` is gitignored, so it required `git add -f .env` to include it in the commit as requested by the brief. This is expected behavior but worth noting for reviewers.
- Pytest was missing from the venv and had to be installed before tests could run. It was installed only inside the project virtual environment.
