# Task 2 Report

## Change
Applied `PickleSafeLoggerMixin` to the core simulation state classes so the `Engine` can be pickled for checkpointing:

- `marble/agent/base_agent.py`
- `marble/graph/agent_graph.py`
- `marble/memory/base_memory.py`
- `marble/memory/shared_memory.py`
- `marble/evaluator/evaluator.py`
- `marble/engine/engine_planner.py`

Also created `tests/test_pickle_safe_classes.py` to verify that the state classes round-trip through `pickle.dumps` / `pickle.loads`.

## Additional Pickle-Safe Handling Discovered During Testing

Two classes required extra `__getstate__` / `__setstate__` logic beyond the mixin:

1. `SharedMemory` (`marble/memory/shared_memory.py`) holds a `threading.Lock`, which is not pickleable. Added custom `__getstate__` to drop the lock and `__setstate__` to recreate it.
2. `BaseAgent` (`marble/agent/base_agent.py`) initializes `self.msg_box` as `defaultdict(lambda: defaultdict(list))`. The nested lambda is not pickleable. Added custom `__getstate__` to convert the `defaultdict` to a plain `dict` for serialization and `__setstate__` to restore it as a `defaultdict` after deserialization.

## Test Note

The test in the brief used a single agent (`agent_id: a1`) with `coding_config_minimal.yaml`, which declares relationships between `agent1` and `agent2`. This caused `AgentGraph.__init__` to raise `ValueError: Source agent 'agent1' does not exist.`. The test was adjusted to create two agents with IDs matching the config (`agent1` and `agent2`), which is the minimal change needed to make the test valid.

## Test Command and Output

```bash
python -m pytest tests/test_pickle_safe_classes.py -v
```

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.1 -- /Users/saptarshi/workfiles/MARBLE/MARBLE/venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/saptarshi/workfiles/MARBLE/MARBLE
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 1 item

tests/test_pickle_safe_classes.py::test_engine_state_classes_are_pickleable PASSED [100%]

============================== 1 passed, 2 warnings in 8.08s ===============================
```

## Commit

- SHA: `b340c61`
- Subject: `feat: make core state classes pickle-safe`

## Follow-up Fix

- File: `marble/memory/shared_memory.py`
- Change: `__getstate__` now delegates to `super().__getstate__()` so `PickleSafeLoggerMixin` drops the logger, then removes the non-pickleable `threading.Lock`. `__setstate__` now calls `super().__setstate__(state)` to recreate the logger before recreating the lock.

### Test Command and Output

```bash
python -m pytest tests/test_pickle_safe_classes.py tests/test_pickle_safe_mixin.py -v
```

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Users/saptarshi/workfiles/MARBLE/MARBLE/venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/saptarshi/workfiles/MARBLE/MARBLE
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 2 items

tests/test_pickle_safe_classes.py::test_engine_state_classes_are_pickleable PASSED [ 50%]
tests/test_pickle_safe_mixin.py::test_pickle_preserves_data_and_recreates_logger PASSED [100%]

============================== 2 passed, 2 warnings in 7.30s ==========================
```

### Follow-up Commit

- SHA: `47473f1`
- Subject: `fix(shared_memory): delegate getstate/setstate to PickleSafeLoggerMixin`
