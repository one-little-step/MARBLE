## Task 3 Report: Timestamped output/log directory manager

**Status:** DONE

### Summary of changes

Created `marble/utils/output_manager.py` to manage timestamped run directories. It provides a `RunPaths` dataclass, directory creation logic, logging setup, and config backup. The module infers a scenario name from the config path (parent directory for nested configs, file stem for top-level configs) and builds a structure under `OUTPUT_ROOT_DIR` (defaulting to `outputs/<scenario>/<timestamp>/`).

Integrated the manager into `marble/main.py` so that every run creates a dedicated directory, redirects logging, backs up the config, and overrides `config.environment["workspace_dir"]` and `config.output["file_path"]` to point into the run directory (only when those keys exist). Updated the two sample YAML configs to use basename-only output file paths so the manager can place them in the run directory. Added unit tests in `tests/test_output_manager.py` covering directory creation and scenario resolution.

### Test command(s) run and their output

```bash
python -m pytest tests/test_output_manager.py -v
```

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.0
rootdir: /Users/saptarshi/workfiles/MARBLE/MARBLE
configfile: pyproject.toml
collected 3 items

tests/test_output_manager.py::TestOutputManager::test_creates_timestamped_directories PASSED [ 33%]
tests/test_output_manager.py::TestOutputManager::test_resolve_scenario_nested PASSED [ 66%]
tests/test_output_manager.py::TestOutputManager::test_resolve_scenario_top_level PASSED [100%]

============================== 3 passed in 0.02s ===============================
```

### Commit hash and message

- **Hash:** `ca6fae66a9f5cc6bd981109bc6a7a9be79a04e54`
- **Message:** `feat: timestamped output/log directories for every run`

### Concerns or blockers

None.
