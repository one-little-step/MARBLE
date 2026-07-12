# Task 3 Report: Add environment checkpoint hooks

## Status
DONE

## Summary
Implemented default `save_checkpoint` / `restore_checkpoint` hooks on `BaseEnvironment` and added a round-trip test.

## Changes
- `marble/environments/base_env.py`:
  - Added `from pathlib import Path` and `import shutil` imports.
  - Made `config` optional (`Optional[Dict[str, Any]] = None`) and default to `{}`.
  - Added `self.workspace_dir: str = config.get("workspace_dir", "workspace")` in `__init__`.
  - Added `save_checkpoint(checkpoint_dir: Path)` that copies `self.workspace_dir` into `checkpoint_dir/workspace/`, creating an empty destination directory when no workspace exists.
  - Added `restore_checkpoint(checkpoint_dir: Path)` that copies `checkpoint_dir/workspace/` back to `self.workspace_dir`, replacing the existing workspace if present.
- `tests/test_checkpoint_resume.py`:
  - Added `test_base_environment_checkpoint_round_trip` demonstrating save, mutation, restore behavior.
  - Note: the brief's import path `marble.environments.base_environment` does not exist in this repo; the file is `marble/environments/base_env.py`, so the test imports from `marble.environments.base_env`.

## Test result
```
$ python -m pytest tests/test_checkpoint_resume.py::test_base_environment_checkpoint_round_trip -v
1 passed
```

## Commit
- `dc1e27d` feat: add default environment checkpoint hooks

## Concerns
- The brief assumes a file named `base_environment.py`, but the repo uses `base_env.py`. Implementation was applied to the actual file, and the test import was adjusted accordingly.
- `BaseEnvironment.__init__` signature was changed to make `config` optional. Existing callers pass both `name` and `config`, so this is backward compatible.
