# Checkpoint / Resume Design for MARBLE

Date: 2026-07-06
Status: Draft pending review

## Goal

Allow a MARBLE simulation run to be interrupted at the point of failure, preserve the exact program state, and resume from that point after the user verifies and rectifies the error. The first milestone is **iteration-level** checkpoint/resume; per-agent checkpoints will be added later using the same machinery.

## Constraints

- Resume must not re-run completed iterations.
- Any exception raised inside a coordination loop must be recoverable.
- Coding, Research, and generic workspace-based environments must work out of the box.
- DB / Minecraft / Web environments must be supportable later via optional hooks without redesign.
- Existing CLI and config behavior must remain unchanged when `--resume_from` is not used.
- Checkpoints must not include API keys or non-serializable client handles.

## Architecture

### Checkpoint boundaries

A checkpoint is taken at the end of every successfully completed iteration in each coordination mode (`star_coordinate`, `graph_coordinate`, `chain_coordinate`, `tree_coordinate`). An **emergency failure checkpoint** is also written when an exception escapes the loop body.

### Checkpoint payload

Each checkpoint directory contains:

- `engine.pkl` — full pickled `Engine` object and its reachable state (config, agents, graph, planner, memory, evaluator, current iteration, results so far).
- `workspace/` — snapshot of the workspace directory at checkpoint time.
- `checkpoint.json` — metadata:
  - `timestamp`
  - `iteration` (or `chain_length` for chain mode)
  - `coordination_mode`
  - `base_dir` of the run
  - `exception` info if this is a failure checkpoint
  - `config_backup_file` path

### Checkpoint storage layout

```
outputs/<scenario>/<timestamp>/
  config.yaml
  logs/marble.log
  workspace/
  development_output.jsonl
  checkpoints/
    iter_000/
      engine.pkl
      workspace/
      checkpoint.json
    iter_001/
      ...
    latest/              -> symlink to most recent iter_NNN
    failure/
      engine.pkl
      workspace/
      checkpoint.json
```

### Resume flow

CLI additions:

```bash
python -m marble.main --config_path marble/configs/coding_config/coding_config_minimal.yaml
python -m marble.main --config_path marble/configs/coding_config/coding_config_minimal.yaml \
  --resume_from outputs/coding_config/20260706-135532/checkpoints/latest
```

On resume:

1. Parse `--resume_from` path.
2. Load `engine.pkl` into a fresh `Engine` instance.
3. Read `checkpoint.json` for metadata.
4. If `--config_path` is also supplied, compare it to the backed-up config and warn if different.
5. Call `engine.restore_from_checkpoint(checkpoint_dir)`:
   - Restore workspace from checkpoint snapshot.
   - Call `environment.restore_checkpoint(checkpoint_dir)` hook.
   - Re-attach logger.
6. Run `engine.resume()` which dispatches to the correct coordination mode and continues from `current_iteration`.

### Environment hooks

Add to `BaseEnvironment`:

```python
def save_checkpoint(self, checkpoint_dir: Path) -> None:
    """Default: copy workspace_dir into checkpoint_dir/workspace/."""

def restore_checkpoint(self, checkpoint_dir: Path) -> None:
    """Default: copy checkpoint_dir/workspace/ back to workspace_dir."""
```

Subclasses override for DB/Minecraft/Web-specific state. The default behavior makes Coding and Research environments work immediately.

### Pickle safety

`Engine`, `BaseAgent`, `AgentGraph`, `BaseMemory`, `SharedMemory`, `EnginePlanner`, and `Evaluator` must be pickleable. `logging.Logger` instances are not pickleable, so affected classes implement `__getstate__` / `__setstate__` to drop and recreate loggers by class name. Any non-pickleable client handles held as instance attributes must be excluded in the same way.

### Failure handling

Each coordination loop body is wrapped in `try/except`. On exception:

1. Write a `checkpoints/failure/` snapshot.
2. Log the exception and checkpoint path.
3. Re-raise so the process exits non-zero.

The user fixes the bug, then reruns with `--resume_from outputs/.../checkpoints/latest` or the explicit `iter_NNN` directory.

## Open Decisions

- **Retention policy**: Keep all iteration checkpoints by default. Add optional config `max_checkpoints` later to prune old checkpoints and limit disk usage.
- **Config on resume**: Allow `--config_path` to be optional when `--resume_from` is provided; fall back to the backed-up config. If both are provided, compare hashes and warn on mismatch.

## Testing Plan

1. Unit test: save and restore a minimal `Engine` after one iteration in `star` mode; assert `current_iteration`, agent results, and workspace are restored.
2. Unit test: verify `BaseEnvironment.save_checkpoint` / `restore_checkpoint` copy workspace contents correctly.
3. Integration test: run a 2-iteration coding config, kill after iteration 1, resume, and verify the final output matches a non-interrupted run.
4. Failure test: inject an exception mid-iteration, verify `checkpoints/failure/` is written, and verify resume from it continues correctly.

## Affected Files

- `marble/main.py` — add `--resume_from` argument, dispatch resume path.
- `marble/engine/engine.py` — add checkpoint save/restore/resume methods, wrap loops with failure checkpointing.
- `marble/environments/base_env.py` — add `save_checkpoint` / `restore_checkpoint` hooks.
- `marble/utils/output_manager.py` — add checkpoint path helpers and symlink management.
- `marble/agent/base_agent.py`, `marble/graph/agent_graph.py`, `marble/memory/*.py`, `marble/evaluator/evaluator.py`, `marble/engine/engine_planner.py` — ensure pickle safety via logger state methods.
- `tests/test_checkpoint_resume.py` — new test file.

## Future Work

- Per-agent / per-action checkpoints inside an iteration.
- Configurable `checkpoint_interval` (e.g., every N iterations) to reduce I/O for long runs.
- Automatic cleanup of old checkpoints via `max_checkpoints`.
