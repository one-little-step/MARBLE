### Task 2: Apply pickle-safe mixin to Engine state classes

**Files:**
- Modify: `marble/agent/base_agent.py`
- Modify: `marble/graph/agent_graph.py`
- Modify: `marble/memory/base_memory.py`
- Modify: `marble/memory/shared_memory.py`
- Modify: `marble/evaluator/evaluator.py`
- Modify: `marble/engine/engine_planner.py`
- Test: `tests/test_pickle_safe_classes.py` (or add to `tests/test_checkpoint_resume.py`)

**Interfaces:**
- Consumes: `PickleSafeLoggerMixin` from Task 1.
- Produces: Each listed class is pickle-safe.

- [ ] **Step 1: Add mixin to classes**

For each file below, make exactly these changes:

`marble/agent/base_agent.py`:
```python
from marble.utils.pickle_safe_mixin import PickleSafeLoggerMixin

class BaseAgent(PickleSafeLoggerMixin):
    ...
```

`marble/graph/agent_graph.py`:
```python
from marble.utils.pickle_safe_mixin import PickleSafeLoggerMixin

class AgentGraph(PickleSafeLoggerMixin):
    ...
```

`marble/memory/base_memory.py`:
```python
from marble.utils.pickle_safe_mixin import PickleSafeLoggerMixin

class BaseMemory(PickleSafeLoggerMixin):
    ...
```

`marble/memory/shared_memory.py`:
```python
from marble.utils.pickle_safe_mixin import PickleSafeLoggerMixin

class SharedMemory(PickleSafeLoggerMixin):
    ...
```

`marble/evaluator/evaluator.py`:
```python
from marble.utils.pickle_safe_mixin import PickleSafeLoggerMixin

class Evaluator(PickleSafeLoggerMixin):
    ...
```

`marble/engine/engine_planner.py`:
```python
from marble.utils.pickle_safe_mixin import PickleSafeLoggerMixin

class EnginePlanner(PickleSafeLoggerMixin):
    ...
```

- [ ] **Step 2: Write the test**

```python
# tests/test_pickle_safe_classes.py
import pickle

from marble.agent.base_agent import BaseAgent
from marble.configs.config import Config
from marble.environments.base_environment import BaseEnvironment
from marble.evaluator.evaluator import Evaluator
from marble.graph.agent_graph import AgentGraph
from marble.memory.base_memory import BaseMemory
from marble.memory.shared_memory import SharedMemory


def test_engine_state_classes_are_pickleable():
    env = BaseEnvironment(name="Test Env", config={"workspace_dir": "/tmp"})
    agent = BaseAgent(config={"agent_id": "a1", "profile": "test"}, env=env)
    config = Config.load("marble/configs/coding_config/coding_config_minimal.yaml")
    graph = AgentGraph([agent], config)
    memory = SharedMemory()
    evaluator = Evaluator(metrics_config={})

    for obj in [env, agent, graph, memory, evaluator]:
        pickled = pickle.dumps(obj)
        restored = pickle.loads(pickled)
        assert restored is not obj
```

- [ ] **Step 3: Run test to verify it passes**

Run: `python -m pytest tests/test_pickle_safe_classes.py -v`

Expected: `1 passed` (or failures that expose additional non-pickleable attributes; fix inline)

- [ ] **Step 4: Commit**

```bash
git add marble/agent/base_agent.py marble/graph/agent_graph.py marble/memory/base_memory.py \
        marble/memory/shared_memory.py marble/evaluator/evaluator.py marble/engine/engine_planner.py \
        tests/test_pickle_safe_classes.py
git commit -m "feat: make core state classes pickle-safe"
```

---

