### Task 1: Reusable pickle-safe mixin for logger-holding classes

**Files:**
- Create: `marble/utils/pickle_safe_mixin.py`
- Test: `tests/test_pickle_safe_mixin.py` (temporary, can be merged into `test_checkpoint_resume.py` later)

**Interfaces:**
- Produces: `class PickleSafeLoggerMixin` with `__getstate__` / `__setstate__` that drops/recreates a logger named after the concrete class.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pickle_safe_mixin.py
import logging
import pickle

from marble.utils.pickle_safe_mixin import PickleSafeLoggerMixin


class DummyClass(PickleSafeLoggerMixin):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.value = 42


def test_pickle_preserves_data_and_recreates_logger():
    obj = DummyClass()
    obj.value = 100
    pickled = pickle.dumps(obj)
    restored = pickle.loads(pickled)
    assert restored.value == 100
    assert restored.logger.name == "DummyClass"
    assert "logger" not in obj.__getstate__()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_pickle_safe_mixin.py -v`

Expected: `ImportError: cannot import name 'PickleSafeLoggerMixin'`

- [ ] **Step 3: Write minimal implementation**

```python
# marble/utils/pickle_safe_mixin.py
"""Mixin that makes logger-holding classes safe to pickle."""
import logging
from typing import Any, Dict


class PickleSafeLoggerMixin:
    """
    Drop the logger during pickling and recreate it on unpickling.
    Any subclass that stores ``self.logger`` should inherit this mixin.
    """

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        if "logger" in state:
            del state["logger"]
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__dict__.update(state)
        self.logger = logging.getLogger(self.__class__.__name__)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_pickle_safe_mixin.py -v`

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add marble/utils/pickle_safe_mixin.py tests/test_pickle_safe_mixin.py
git commit -m "feat: add PickleSafeLoggerMixin for checkpoint serialization"
```

---

