# Task 1 Report

## Change
Fixed the assertion in `tests/test_pickle_safe_mixin.py`.

Previously the test asserted `restored.logger is not obj.logger`, which cannot pass because `logging.getLogger` returns a singleton per logger name.

Replaced it with:

```python
assert "logger" not in obj.__getstate__()
```

This verifies the actual behavior of `PickleSafeLoggerMixin`: the logger is excluded from the pickled state.

## Test Command and Output
```bash
python -m pytest tests/test_pickle_safe_mixin.py -v
```

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-0.13.1
rootdir: /Users/saptarshi/workfiles/MARBLE/MARBLE
collecting ... collected 1 item

tests/test_pickle_safe_mixin.py::test_pickle_preserves_data_and_recreates_logger PASSED [100%]

============================== 1 passed in 0.03s ===============================
```

## Commit
- SHA: `977af71`
- Subject: `fix: test pickle-safe mixin by asserting logger excluded from state`
