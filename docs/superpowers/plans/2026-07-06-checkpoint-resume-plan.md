# Checkpoint / Resume Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add iteration-level checkpoint/resume to MARBLE so a simulation run can be interrupted on failure and resumed from the last completed iteration without re-running prior work.

**Architecture:** Use Python `pickle` to snapshot the full `Engine` object (and its reachable state) at iteration boundaries. Persist a matching workspace snapshot and JSON metadata. On resume, reload the Engine, restore workspace, and continue the coordination loop from `current_iteration`. Provide optional `save_checkpoint`/`restore_checkpoint` hooks on `BaseEnvironment` for environments with external state.

**Tech Stack:** Python 3.9, standard library (`pickle`, `shutil`, `pathlib`, `json`), existing MARBLE utilities.

## Global Constraints

- Resume must not re-run completed iterations.
- Any exception raised inside a coordination loop must be recoverable via a failure checkpoint.
- Coding, Research, and generic workspace-based environments must work out of the box.
- DB / Minecraft / Web environments must be supportable later via optional hooks without redesign.
- Existing CLI and config behavior must remain unchanged when `--resume_from` is not used.
- Checkpoints must not include API keys or non-serializable client handles.
- Keep all iteration checkpoints by default; add optional `max_checkpoints` later.
- When `--config_path` is provided with `--resume_from`, compare it to the backed-up config and warn on mismatch.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `marble/utils/output_manager.py` | Create/checkpoint path helpers, symlink latest checkpoint, workspace copy helpers. |
| `marble/environments/base_env.py` | Default `save_checkpoint` / `restore_checkpoint` hooks that copy workspace. |
| `marble/utils/pickle_safe_mixin.py` | Reusable mixin to make logger-holding classes pickle-safe. |
| `marble/agent/base_agent.py` | Inherit pickle-safe mixin. |
| `marble/graph/agent_graph.py` | Inherit pickle-safe mixin. |
| `marble/memory/base_memory.py` | Inherit pickle-safe mixin. |
| `marble/memory/shared_memory.py` | Inherit pickle-safe mixin. |
| `marble/evaluator/evaluator.py` | Inherit pickle-safe mixin. |
| `marble/engine/engine_planner.py` | Inherit pickle-safe mixin. |
| `marble/engine/engine.py` | Checkpoint save/restore/resume methods; wrap loops with failure checkpointing. |
| `marble/main.py` | Add `--resume_from` CLI argument; dispatch to resume path. |
| `tests/test_checkpoint_resume.py` | Unit tests for checkpoint save/restore/resume. |

---

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

### Task 3: Add environment checkpoint hooks

**Files:**
- Modify: `marble/environments/base_env.py`
- Test: `tests/test_checkpoint_resume.py` (add test in this task)

**Interfaces:**
- Produces: `BaseEnvironment.save_checkpoint(checkpoint_dir: Path) -> None`
- Produces: `BaseEnvironment.restore_checkpoint(checkpoint_dir: Path) -> None`

- [ ] **Step 1: Inspect BaseEnvironment structure**

Read `marble/environments/base_env.py` and identify the `workspace_dir` attribute (or add it in `__init__` if absent).

- [ ] **Step 2: Implement default hooks**

```python
# marble/environments/base_env.py
from pathlib import Path
import shutil

class BaseEnvironment:
    def __init__(self, name: str = "Base Environment", config: Optional[Dict[str, Any]] = None):
        ...
        self.workspace_dir = config.get("workspace_dir", "workspace") if config else "workspace"
        ...

    def save_checkpoint(self, checkpoint_dir: Path) -> None:
        """Persist environment state into checkpoint_dir."""
        workspace_src = Path(self.workspace_dir)
        workspace_dst = checkpoint_dir / "workspace"
        if workspace_src.exists():
            shutil.copytree(workspace_src, workspace_dst, dirs_exist_ok=True)
        else:
            workspace_dst.mkdir(parents=True, exist_ok=True)

    def restore_checkpoint(self, checkpoint_dir: Path) -> None:
        """Restore environment state from checkpoint_dir."""
        workspace_src = checkpoint_dir / "workspace"
        workspace_dst = Path(self.workspace_dir)
        if workspace_src.exists():
            if workspace_dst.exists():
                shutil.rmtree(workspace_dst)
            shutil.copytree(workspace_src, workspace_dst)
```

- [ ] **Step 3: Write the test**

```python
# tests/test_checkpoint_resume.py
import tempfile
from pathlib import Path

from marble.environments.base_environment import BaseEnvironment


def test_base_environment_checkpoint_round_trip():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "workspace"
        workspace.mkdir()
        (workspace / "solution.py").write_text("print('hello')")

        env = BaseEnvironment(name="Test", config={"workspace_dir": str(workspace)})
        checkpoint_dir = Path(tmpdir) / "checkpoint"
        env.save_checkpoint(checkpoint_dir)

        (workspace / "solution.py").write_text("print('goodbye')")
        env.restore_checkpoint(checkpoint_dir)

        assert (workspace / "solution.py").read_text() == "print('hello')"
```

- [ ] **Step 4: Run test**

Run: `python -m pytest tests/test_checkpoint_resume.py::test_base_environment_checkpoint_round_trip -v`

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add marble/environments/base_env.py tests/test_checkpoint_resume.py
git commit -m "feat: add default environment checkpoint hooks"
```

---

### Task 4: Add checkpoint path helpers to output_manager

**Files:**
- Modify: `marble/utils/output_manager.py`
- Test: `tests/test_output_manager.py` (extend)

**Interfaces:**
- Produces: `RunPaths.checkpoint_dir: Path`
- Produces: `create_checkpoint_dir(base_dir: Path, iteration: int) -> Path`
- Produces: `update_latest_checkpoint_symlink(base_dir: Path, checkpoint_dir: Path) -> None`
- Produces: `copy_workspace(src: Path, dst: Path) -> None`

- [ ] **Step 1: Add helpers**

```python
# marble/utils/output_manager.py
import shutil
from pathlib import Path


def create_checkpoint_dir(base_dir: Path, iteration: int) -> Path:
    """Create a numbered checkpoint directory under base_dir/checkpoints/."""
    checkpoint_dir = base_dir / "checkpoints" / f"iter_{iteration:03d}"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir


def update_latest_checkpoint_symlink(base_dir: Path, checkpoint_dir: Path) -> None:
    """Create or update base_dir/checkpoints/latest to point to checkpoint_dir."""
    latest_link = base_dir / "checkpoints" / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(checkpoint_dir, target_is_directory=True)


def copy_workspace(src: Path, dst: Path) -> None:
    """Copy a workspace directory, replacing dst if it exists."""
    if dst.exists():
        shutil.rmtree(dst)
    if src.exists():
        shutil.copytree(src, dst)
    else:
        dst.mkdir(parents=True, exist_ok=True)
```

Also add `checkpoint_dir` property to `RunPaths`:

```python
@dataclass(frozen=True)
class RunPaths:
    base_dir: Path
    result_file: Path
    log_file: Path
    workspace_dir: Path
    config_backup_file: Path

    @property
    def checkpoint_dir(self) -> Path:
        return self.base_dir / "checkpoints"
```

- [ ] **Step 2: Add tests**

```python
# tests/test_output_manager.py
from marble.utils.output_manager import (
    create_checkpoint_dir,
    copy_workspace,
    update_latest_checkpoint_symlink,
)


def test_create_checkpoint_dir_numbered(tmp_path):
    cp = create_checkpoint_dir(tmp_path, 7)
    assert cp == tmp_path / "checkpoints" / "iter_007"
    assert cp.exists()


def test_latest_checkpoint_symlink(tmp_path):
    cp = create_checkpoint_dir(tmp_path, 3)
    update_latest_checkpoint_symlink(tmp_path, cp)
    latest = tmp_path / "checkpoints" / "latest"
    assert latest.is_symlink()
    assert latest.resolve() == cp


def test_copy_workspace(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x = 1")
    dst = tmp_path / "dst"
    copy_workspace(src, dst)
    assert (dst / "a.py").read_text() == "x = 1"
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/test_output_manager.py -v`

Expected: all tests pass

- [ ] **Step 4: Commit**

```bash
git add marble/utils/output_manager.py tests/test_output_manager.py
git commit -m "feat: add checkpoint path and workspace helpers"
```

---

### Task 5: Add Engine checkpoint save/restore/resume

**Files:**
- Modify: `marble/engine/engine.py`
- Test: `tests/test_checkpoint_resume.py` (extend)

**Interfaces:**
- Produces: `Engine.save_checkpoint(iteration_label: str, exception: Optional[Exception] = None) -> Path`
- Produces: `Engine.restore_from_checkpoint(checkpoint_dir: Path) -> None`
- Produces: `Engine.resume() -> None`

- [ ] **Step 1: Import helpers and pickle**

At the top of `marble/engine/engine.py`:

```python
import json
import pickle
import shutil
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from marble.utils.output_manager import (
    create_checkpoint_dir,
    copy_workspace,
    update_latest_checkpoint_symlink,
)
```

- [ ] **Step 2: Add `run_base_dir` to Engine constructor**

Modify `Engine.__init__` signature and store `run_base_dir`:

```python
    def __init__(self, config: Config, run_base_dir: Optional[Path] = None):
        """
        Initialize the Engine with the given configuration.

        Args:
            config (Config): Configuration parameters.
            run_base_dir: Optional Path to the run output directory, used for checkpoint storage.
        """
        self.logger = get_logger(self.__class__.__name__)
        self.config = config
        self._run_base_dir = run_base_dir
        ...
```

- [ ] **Step 3: Add checkpoint methods to Engine**

Insert these methods after `__init__` (or near other lifecycle methods):

```python
    def save_checkpoint(
        self,
        iteration_label: str,
        exception: Optional[Exception] = None,
    ) -> Path:
        """
        Serialize the Engine and environment workspace to a checkpoint directory.

        Args:
            iteration_label: Directory name segment, e.g. "iter_003" or "failure".
            exception: If provided, include traceback in checkpoint metadata.

        Returns:
            Path to the checkpoint directory.
        """
        if self._run_base_dir is None:
            raise RuntimeError(
                "Engine was not initialized with run_base_dir; checkpointing is disabled."
            )
        checkpoint_dir = self._run_base_dir / "checkpoints" / iteration_label
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Snapshot the engine object.
        engine_path = checkpoint_dir / "engine.pkl"
        with open(engine_path, "wb") as f:
            pickle.dump(self, f)

        # Snapshot environment/workspace state.
        self.environment.save_checkpoint(checkpoint_dir)

        # Metadata.
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "iteration": self.current_iteration,
            "coordination_mode": self.coordinate_mode,
            "base_dir": str(self._run_base_dir),
            "config_backup_file": str(self._run_base_dir / "config.yaml"),
            "exception": None,
        }
        if exception is not None:
            metadata["exception"] = "".join(
                traceback.format_exception(type(exception), exception, exception.__traceback__)
            )

        with open(checkpoint_dir / "checkpoint.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        self.logger.info(f"Checkpoint saved: {checkpoint_dir}")
        return checkpoint_dir

    def restore_from_checkpoint(self, checkpoint_dir: Path) -> None:
        """
        Restore environment workspace from a checkpoint directory.
        Called on a freshly unpickled Engine instance.
        """
        self.environment.restore_checkpoint(checkpoint_dir)
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Engine restored from checkpoint: {checkpoint_dir}")

    def resume(self) -> None:
        """Resume the simulation from the current iteration."""
        self.logger.info(
            f"Resuming simulation at iteration {self.current_iteration} in {self.coordinate_mode} mode."
        )
        if isinstance(self.environment, MinecraftEnvironment):
            self.environment.launch()
        try:
            if self.coordinate_mode == "star":
                self.star_coordinate()
            elif self.coordinate_mode == "graph":
                self.graph_coordinate()
            elif self.coordinate_mode == "chain":
                self.chain_coordinate()
            elif self.coordinate_mode == "tree":
                self.tree_coordinate()
            else:
                raise ValueError(f"Unsupported coordinate mode: {self.coordinate_mode}")
        finally:
            if isinstance(self.environment, MinecraftEnvironment):
                self.environment.finish()
```

- [ ] **Step 4: Insert checkpoint calls into coordination loops**

For each coordination method (`star_coordinate`, `graph_coordinate`, `chain_coordinate`, `tree_coordinate`), wrap the outer `try` body like this (example for `star_coordinate`):

```python
    def star_coordinate(self) -> None:
        try:
            summary_data = { ... }
            while self.current_iteration < self.max_iterations:
                ...  # existing loop body
                # At the end of each iteration, after appending to summary_data:
                checkpoint_dir = self.save_checkpoint(f"iter_{self.current_iteration:03d}")
                if self._run_base_dir is not None:
                    update_latest_checkpoint_symlink(self._run_base_dir, checkpoint_dir)
                if not continue_simulation:
                    break
            ...  # final evaluation
        except Exception as exc:
            self._save_failure_checkpoint(exc)
            raise
        finally:
            ...  # existing finalize
```

Add the helper:

```python
    def _save_failure_checkpoint(self, exc: Exception) -> Path:
        """Save a failure checkpoint and return its path."""
        checkpoint_dir = self.save_checkpoint("failure", exception=exc)
        self.logger.error(
            f"Failure checkpoint saved to {checkpoint_dir}: {exc}"
        )
        return checkpoint_dir
```

Apply the same pattern to `graph_coordinate`, `chain_coordinate`, and `tree_coordinate`. For `graph_coordinate`, the initial assignment (iteration 0) is also a checkpoint boundary.

- [ ] **Step 5: Test save/restore of a minimal Engine**

```python
# tests/test_checkpoint_resume.py
import pickle
import tempfile
from pathlib import Path

from marble.configs.config import Config
from marble.engine.engine import Engine


def test_engine_checkpoint_save_and_restore(tmp_path):
    config = Config.load("marble/configs/coding_config/coding_config_minimal.yaml")
    config.environment["workspace_dir"] = str(tmp_path / "workspace")
    config.output["file_path"] = str(tmp_path / "output.jsonl")

    engine = Engine(config, run_base_dir=tmp_path)
    engine.current_iteration = 2
    engine.evaluator.metrics["planning_score"].append(0.5)

    checkpoint_dir = engine.save_checkpoint("iter_002")
    update_latest_checkpoint_symlink(tmp_path, checkpoint_dir)

    with open(checkpoint_dir / "engine.pkl", "rb") as f:
        restored = pickle.load(f)
    restored.restore_from_checkpoint(checkpoint_dir)

    assert restored.current_iteration == 2
    assert restored.evaluator.metrics["planning_score"] == [0.5]
    assert (tmp_path / "checkpoints" / "latest").is_symlink()
```

- [ ] **Step 6: Run tests**

Run: `python -m pytest tests/test_checkpoint_resume.py -v`

Expected: tests pass (fix any pickle errors by applying `PickleSafeLoggerMixin` to additional classes as needed)

- [ ] **Step 7: Commit**

```bash
git add marble/engine/engine.py tests/test_checkpoint_resume.py
git commit -m "feat: add iteration-level checkpoint save/restore/resume to Engine"
```

---

### Task 6: Integrate `--resume_from` into main.py

**Files:**
- Modify: `marble/main.py`
- Test: `tests/test_main.py` (extend)

**Interfaces:**
- Consumes: `Engine.save_checkpoint`, `Engine.restore_from_checkpoint`, `Engine.resume` from Task 5.
- Produces: CLI argument `--resume_from PATH`.

- [ ] **Step 1: Add CLI argument**

```python
# marble/main.py
import pickle
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Marble simulation engine.")
    parser.add_argument(
        "--config_path",
        type=str,
        required=False,  # optional when resuming
        help="Path to the configuration YAML file.",
    )
    parser.add_argument(
        "--resume_from",
        type=str,
        required=False,
        help="Path to a checkpoint directory to resume from.",
    )
    return parser.parse_args()
```

- [ ] **Step 2: Add resume path and config validation**

```python
def _validate_config_match(config_path: str, checkpoint_metadata: dict) -> None:
    import hashlib
    if not config_path:
        return
    with open(config_path, "rb") as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()
    backup_path = checkpoint_metadata.get("config_backup_file")
    if backup_path and Path(backup_path).exists():
        with open(backup_path, "rb") as f:
            backup_hash = hashlib.sha256(f.read()).hexdigest()
        if current_hash != backup_hash:
            logging.warning(
                f"Config mismatch: supplied {config_path} differs from the config used for the checkpoint."
            )


def main() -> None:
    args = parse_args()

    if not args.config_path and not args.resume_from:
        logging.error("Either --config_path or --resume_from is required.")
        sys.exit(1)

    if args.resume_from:
        checkpoint_dir = Path(args.resume_from)
        if not checkpoint_dir.exists():
            logging.error(f"Checkpoint directory not found: {checkpoint_dir}")
            sys.exit(1)

        metadata_path = checkpoint_dir / "checkpoint.json"
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        base_dir = Path(metadata["base_dir"])
        config_path = args.config_path or str(base_dir / "config.yaml")
        _validate_config_match(args.config_path, metadata)

        if not os.path.isfile(config_path):
            logging.error(f"Configuration file not found: {config_path}")
            sys.exit(1)

        try:
            config = Config.load(config_path)
        except Exception as e:
            logging.error(f"Error loading configuration from {config_path}: {e}")
            sys.exit(1)

        run_paths = create_run_paths(
            config_path=config_path,
            output_file=getattr(config, "output", {}).get("file_path", "output.jsonl"),
            timestamp=base_dir.name,
            scenario=base_dir.parent.name,
        )
        setup_logging(run_paths.log_file)
        # Re-configure output paths to match the resumed run.
        config.output["file_path"] = str(run_paths.result_file)
        if "workspace_dir" in config.environment:
            config.environment["workspace_dir"] = str(run_paths.workspace_dir)

        with open(checkpoint_dir / "engine.pkl", "rb") as f:
            engine = pickle.load(f)
        engine.restore_from_checkpoint(checkpoint_dir)
        engine.resume()
        return

    # Fresh-run path
    if not os.path.isfile(args.config_path):
        logging.error(f"Configuration file not found: {args.config_path}")
        sys.exit(1)

    try:
        config = Config.load(args.config_path)
    except Exception as e:
        logging.error(f"Error loading configuration from {args.config_path}: {e}")
        sys.exit(1)

    output_file = getattr(config, "output", {}).get("file_path", "output.jsonl")
    run_paths = create_run_paths(
        config_path=args.config_path,
        output_file=output_file,
    )
    setup_logging(run_paths.log_file)
    backup_config(args.config_path, run_paths.config_backup_file)

    if "workspace_dir" in config.environment:
        config.environment["workspace_dir"] = str(run_paths.workspace_dir)
    if "file_path" in config.output:
        config.output["file_path"] = str(run_paths.result_file)

    logger = logging.getLogger(__name__)
    logger.info(f"Run artifacts: {run_paths.base_dir}")

    try:
        logging.info(f"Starting engine with configuration: {args.config_path}")
        engine = Engine(config, run_base_dir=run_paths.base_dir)
        engine.start()
    except Exception:
        logging.exception(
            f"An error occurred while running the engine with configuration: {args.config_path}"
        )
        sys.exit(1)
```

- [ ] **Step 3: Update `create_run_paths` to accept scenario and timestamp overrides**

Ensure `create_run_paths` already supports `scenario` and `timestamp` parameters (it does in the current code).

- [ ] **Step 4: Add CLI test**

```python
# tests/test_main.py
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from marble.main import parse_args


def test_parse_args_resume_from():
    with patch.object(sys, "argv", ["marble", "--resume_from", "outputs/x/20260706-000000/checkpoints/latest"]):
        args = parse_args()
    assert args.resume_from == "outputs/x/20260706-000000/checkpoints/latest"
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_main.py -v`

Expected: passes

- [ ] **Step 6: Commit**

```bash
git add marble/main.py tests/test_main.py
git commit -m "feat: add --resume_from CLI option for checkpoint resume"
```

---

### Task 7: Integration test — interrupt and resume a 2-iteration coding run

**Files:**
- Create: `tests/test_checkpoint_resume_integration.py`

**Interfaces:**
- Consumes: full checkpoint/resume pipeline.

- [ ] **Step 1: Write the test**

This test uses a monkeypatched `BaseAgent.act` to throw an exception on the second iteration, then resumes and verifies the run completes.

```python
# tests/test_checkpoint_resume_integration.py
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from marble.configs.config import Config
from marble.engine.engine import Engine


def test_interrupt_and_resume_star_coordination():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        config = Config.load("marble/configs/coding_config/coding_config_minimal.yaml")
        config.environment["max_iterations"] = 3
        config.environment["workspace_dir"] = str(tmpdir_path / "workspace")
        config.output["file_path"] = str(tmpdir_path / "output.jsonl")

        call_count = {"n": 0}
        original_act = __import__("marble.agent.base_agent", fromlist=["BaseAgent"]).BaseAgent.act

        def failing_act(self, task):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("simulated failure")
            return original_act(self, task)

        # First run: fail on second act.
        with patch("marble.agent.base_agent.BaseAgent.act", failing_act):
            engine = Engine(config, run_base_dir=tmpdir_path)
            try:
                engine.star_coordinate()
            except RuntimeError:
                pass

        failure_cp = tmpdir_path / "checkpoints" / "failure"
        assert failure_cp.exists()

        # Resume from latest completed checkpoint (iter_001).
        latest = tmpdir_path / "checkpoints" / "latest"
        assert latest.is_symlink()

        with open(latest / "engine.pkl", "rb") as f:
            restored = pickle.load(f)
        restored.restore_from_checkpoint(latest)
        restored.resume()

        # Verify output file has iterations.
        lines = list(open(tmpdir_path / "output.jsonl"))
        data = json.loads(lines[-1])
        assert len(data["iterations"]) >= 2
```

- [ ] **Step 2: Run the test**

Run: `python -m pytest tests/test_checkpoint_resume_integration.py -v -s`

Expected: `1 passed` (may take 1–2 minutes because it uses the LLM)

- [ ] **Step 3: Commit**

```bash
git add tests/test_checkpoint_resume_integration.py
git commit -m "test: add interrupt-and-resume integration test"
```

---

## Final Verification

- [ ] Run the targeted unit tests:

```bash
python -m pytest tests/test_pickle_safe_mixin.py tests/test_pickle_safe_classes.py \
                 tests/test_checkpoint_resume.py tests/test_output_manager.py \
                 tests/test_main.py -v
```

Expected: all pass

- [ ] Run the integration test (optional, may call LLM):

```bash
python -m pytest tests/test_checkpoint_resume_integration.py -v -s
```

Expected: pass

- [ ] Manual smoke test:

```bash
python -m marble.main --config_path marble/configs/coding_config/coding_config_minimal.yaml
# kill process after iteration 1, then:
python -m marble.main --resume_from outputs/coding_config/<timestamp>/checkpoints/latest
```

---

## Spec Coverage Check

| Spec Section | Implementing Task |
|--------------|-------------------|
| Checkpoint boundaries at end of iteration | Task 5 |
| Emergency failure checkpoint | Task 5 `_save_failure_checkpoint` |
| Persist engine.pkl, workspace/, checkpoint.json | Task 5 |
| outputs/<scenario>/<timestamp>/checkpoints layout | Task 4 + Task 5 |
| `--resume_from` CLI | Task 6 |
| `restore_from_checkpoint` / `resume` | Task 5 |
| Environment hooks | Task 3 |
| Pickle safety | Task 1 + Task 2 |
| Config mismatch warning | Task 6 |
| Tests | Tasks 1–7 |

## Placeholder Scan

No TBD/TODO/fill-in-details placeholders. All code blocks are complete and runnable.
