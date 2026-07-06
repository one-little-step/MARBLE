### Task 3: Create timestamped output/log directory manager

**Files:**
- Create: `marble/utils/output_manager.py`
- Modify: `marble/main.py`
- Modify: `marble/configs/coding_config/coding_config.yaml`
- Modify: `marble/configs/test_config_research/profile_1.yaml`
- Test: `tests/test_output_manager.py`

**Interfaces:**
- Consumes: scenario name, config `output.file_path`, optional `OUTPUT_ROOT_DIR` env var
- Produces: `RunPaths` dataclass with `base_dir`, `result_file`, `log_file`, `workspace_dir`, `config_backup_file`

- [ ] **Step 1: Implement output manager**

Create `marble/utils/output_manager.py`:

```python
import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class RunPaths:
    """Paths for a single simulation run."""

    base_dir: Path
    result_file: Path
    log_file: Path
    workspace_dir: Path
    config_backup_file: Path

    @property
    def log_dir(self) -> Path:
        return self.log_file.parent


def resolve_scenario(config_path: str) -> str:
    """Infer scenario name from config file path."""
    path = Path(config_path)
    # Use the parent directory name if the file is nested, otherwise the stem.
    if path.parent.name in ("configs", "marble"):
        return path.stem
    return path.parent.name


def create_run_paths(
    config_path: str,
    scenario: Optional[str] = None,
    output_file: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> RunPaths:
    """
    Create timestamped directories for a simulation run.

    Args:
        config_path: Path to the config file being run.
        scenario: Optional scenario name override.
        output_file: Optional relative output file path from the config.
        timestamp: Optional timestamp override (defaults to now).

    Returns:
        RunPaths with all resolved directories and files.
    """
    root = Path(os.environ.get("OUTPUT_ROOT_DIR", "outputs"))
    scenario_name = scenario or resolve_scenario(config_path)
    ts = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    base_dir = root / scenario_name / ts
    base_dir.mkdir(parents=True, exist_ok=True)

    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    workspace_dir = base_dir / "workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    if output_file:
        result_file = base_dir / Path(output_file).name
    else:
        result_file = base_dir / "output.jsonl"

    config_backup = base_dir / "config.yaml"

    return RunPaths(
        base_dir=base_dir,
        result_file=result_file,
        log_file=log_dir / "marble.log",
        workspace_dir=workspace_dir,
        config_backup_file=config_backup,
    )


def setup_logging(log_file: Path, level: int = logging.INFO) -> None:
    """Configure root logger to write to both file and stdout."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="a"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def backup_config(config_path: str, dest: Path) -> None:
    """Copy the used config into the run directory for reproducibility."""
    shutil.copy2(config_path, dest)
```

- [ ] **Step 2: Integrate into `marble/main.py`**

At the top of `marble/main.py`, add:

```python
from marble.utils.output_manager import create_run_paths, setup_logging, backup_config
```

After config is loaded (around where `config` is available), add:

```python
    output_file = getattr(config, "output", {}).get("file_path", "output.jsonl")
    run_paths = create_run_paths(
        config_path=args.config,
        output_file=output_file,
    )
    setup_logging(run_paths.log_file)
    backup_config(args.config, run_paths.config_backup_file)

    # Override workspace and output paths so artifacts land in the run directory.
    config.environment["workspace_dir"] = str(run_paths.workspace_dir)
    config.output["file_path"] = str(run_paths.result_file)

    logger = logging.getLogger(__name__)
    logger.info(f"Run artifacts: {run_paths.base_dir}")
```

Wrap this in a safe check: only mutate paths if those keys exist.

- [ ] **Step 3: Update YAML output paths to be basename-only**

In `marble/configs/coding_config/coding_config.yaml`, change:

```yaml
output:
  format: jsonl
  file_path: "result/development_output.jsonl"
```

to:

```yaml
output:
  format: jsonl
  file_path: "development_output.jsonl"
```

In `marble/configs/test_config_research/profile_1.yaml`, change:

```yaml
output:
  file_path: result/discussion_output.jsonl
  format: jsonl
```

to:

```yaml
output:
  file_path: discussion_output.jsonl
  format: jsonl
```

- [ ] **Step 4: Write unit tests**

Create `tests/test_output_manager.py`:

```python
import os
import tempfile
from pathlib import Path

from marble.utils.output_manager import create_run_paths, resolve_scenario


class TestOutputManager:
    def test_creates_timestamped_directories(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.setenv("OUTPUT_ROOT_DIR", tmp)
            paths = create_run_paths(
                config_path="marble/configs/coding_config/coding_config.yaml",
                output_file="development_output.jsonl",
                timestamp="20250706-120000",
            )
            assert paths.base_dir == Path(tmp) / "coding_config" / "20250706-120000"
            assert paths.result_file == paths.base_dir / "development_output.jsonl"
            assert paths.log_file == paths.base_dir / "logs" / "marble.log"
            assert paths.workspace_dir == paths.base_dir / "workspace"
            assert paths.base_dir.exists()
            assert paths.log_file.parent.exists()
            assert paths.workspace_dir.exists()

    def test_resolve_scenario_nested(self):
        assert resolve_scenario("marble/configs/test_config_research/profile_1.yaml") == "test_config_research"

    def test_resolve_scenario_top_level(self):
        assert resolve_scenario("marble/configs/coding_config.yaml") == "coding_config"
```

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_output_manager.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add marble/utils/output_manager.py marble/main.py marble/configs/coding_config/coding_config.yaml marble/configs/test_config_research/profile_1.yaml tests/test_output_manager.py
git commit -m "feat: timestamped output/log directories for every run"
```

---

