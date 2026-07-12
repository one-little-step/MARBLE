### Task 3: Add environment checkpoint hooks

**Files:**
- Modify: `marble/environments/base_environment.py`
- Test: `tests/test_checkpoint_resume.py` (add test in this task)

**Interfaces:**
- Produces: `BaseEnvironment.save_checkpoint(checkpoint_dir: Path) -> None`
- Produces: `BaseEnvironment.restore_checkpoint(checkpoint_dir: Path) -> None`

- [ ] **Step 1: Inspect BaseEnvironment structure**

Read `marble/environments/base_environment.py` and identify the `workspace_dir` attribute (or add it in `__init__` if absent).

- [ ] **Step 2: Implement default hooks**

```python
# marble/environments/base_environment.py
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
git add marble/environments/base_environment.py tests/test_checkpoint_resume.py
git commit -m "feat: add default environment checkpoint hooks"
```

---

