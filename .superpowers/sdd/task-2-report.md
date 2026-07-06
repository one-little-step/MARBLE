## Task 2 Report

### Status
DONE

### Summary of Changes
- Modified `marble/environments/coding_utils/coder.py` to allow `create_solution_handler` to overwrite an existing `solution.py` when it is empty (size 0), while still refusing to overwrite non-empty files. Also replaced the hardcoded `max_token_num=4096` with `get_max_token_num(default=4096)` and added the corresponding import from `marble.llms.token_config`.
- Updated `marble/environments/coding_utils/reviewer.py` and `marble/environments/coding_utils/debugger.py` to import `get_max_token_num` and use it for all `model_prompting` calls (defaulting to 4096 and 2048 respectively), so coding helpers respect the environment token budget.
- Added `tests/test_coding_recovery.py` with two unit tests: one verifying that an empty existing `solution.py` is allowed through, and another verifying that a non-empty existing `solution.py` is refused.

### Test Command(s) Run and Output
```bash
python -m pytest tests/test_coding_recovery.py -v
```

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.0.0 -- /Users/saptarshi/workfiles/MARBLE/MARBLE/venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/saptarshi/workfiles/MARBLE/MARBLE
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 2 items

tests/test_coding_recovery.py::TestCodingRecovery::test_overwrites_empty_solution PASSED [ 50%]
tests/test_coding_recovery.py::TestCodingRecovery::test_refuses_non_empty_solution PASSED [100%]

======================== 2 passed, 2 warnings in 6.17s =========================
```

### Commit Hash and Message
- **Hash:** `42fb6a5f37eb1fad73e186249daa86d0a7149da8`
- **Message:** `feat: coding tools use env token budget and overwrite empty solution.py`

### Concerns or Blockers
None.
