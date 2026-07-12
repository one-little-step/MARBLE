# Running MARBLE Simulations

## Prerequisites

```bash
# Activate virtual environment
source venv/bin/activate
```

**API Credentials & LLM Source:** Automatically loaded from `.env` file in project root. No manual export needed.

Set the active provider with `LLM_SOURCE` in `.env`:

```bash
# Use the OpenAI-compatible provider (opencode.ai -> deepseek-v4-flash)
LLM_SOURCE=openai

# Or use IBM RITS (Kimi-K2.7-Code)
LLM_SOURCE=rits
```

**`.env` template:**

```bash
LLM_SOURCE=openai

OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://opencode.ai/zen/go/v1
OPENAI_MODEL_NAME=openai/deepseek-v4-flash

RITS_API_KEY=...
RITS_BASE_URL=https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com/moonshotai-kimi-k2-7/v1
RITS_MODEL_NAME=moonshotai/Kimi-K2.7-Code

# Global output token budget (optional). Callers that opt in via
# get_max_token_num(default=...) will use this value when set.
MAX_OUTPUT_TOKENS=4096
```

**How it works:**
- Every LLM call in MARBLE now goes through `marble.llms.client_factory`.
- `LLM_SOURCE` selects which credentials and model name are used.
- Config files no longer need hardcoded `llm` / `model_name` / `evaluate_llm` values; leave them empty (`""`) to let `.env` drive the choice.
- Werewolf no longer reads credentials from `werewolf_config.yaml`; it uses the same factory.

## Output Organization

Every run of `python marble/main.py --config_path <config>` now creates a timestamped directory under `outputs/`:

```
outputs/<scenario>/<YYYYMMDD-HHMMSS>/
├── config.yaml              # copy of the config used for this run
├── development_output.jsonl # or discussion_output.jsonl, etc.
├── logs/
│   └── marble.log           # full stdout + file log for the run
├── workspace/               # coding workspace (solution.py lives here)
└── checkpoints/             # per-iteration Engine snapshots for resume
    ├── iter_001/
    │   ├── engine.pkl       # pickled Engine state
    │   ├── checkpoint.json  # metadata (timestamp, iteration, exception if any)
    │   └── workspace/       # workspace snapshot at end of iteration
    ├── iter_002/
    │   └── ...
    └── latest -> iter_001   # relative symlink to most recent successful checkpoint
```

- `<scenario>` is inferred from the config path (e.g., `coding_config`, `test_config_research`).
- Set `OUTPUT_ROOT_DIR` in the environment to change the root from `outputs/`.
- Config `output.file_path` should be a basename only; the manager places it in the run directory.

### Checkpoint & Resume

MARBLE saves a checkpoint at the end of every successfully completed iteration. If a run fails or is interrupted, you can resume from the latest checkpoint:

```bash
python -m marble.main \
  --config_path marble/configs/coding_config/coding_config_minimal.yaml \
  --resume_from outputs/coding_config/<YYYYMMDD-HHMMSS>/checkpoints/latest
```

- `--resume_from` loads the pickled Engine and restores the workspace snapshot, then continues from `current_iteration` without re-running completed iterations.
- If `--config_path` and `--resume_from` are both supplied, MARBLE compares the config hash against the checkpoint metadata and warns on mismatch.
- The `latest` symlink is relative and cwd-independent, so it resolves correctly from any directory.
- Failure checkpoints are written to `checkpoints/failure/`; they do **not** overwrite `latest`.

**Note:** Checkpoint support currently works out of the box for coding, research, and other workspace-based scenarios. Database, Minecraft, web, and werewolf scenarios use the default workspace-copy hook; custom checkpoint logic for external state can be added by overriding `BaseEnvironment.save_checkpoint()` / `restore_checkpoint()`.

## Scenarios

### Research (5 agents brainstorming)

```bash
python marble/main.py --config_path marble/configs/test_config_research/profile_1.yaml
```

**Config files:** `marble/configs/test_config_research/profile_{1,2,3}.yaml`
**Minimal smoke config:** `marble/configs/test_config_research/profile_1_minimal.yaml`
**Final outputs:**
- `outputs/test_config_research/<timestamp>/discussion_output.jsonl` — full conversation and research idea
- `outputs/test_config_research/<timestamp>/logs/marble.log` — full run log

---

### Coding (software development task)

```bash
python marble/main.py --config_path marble/configs/coding_config/coding_config.yaml
```

**Minimal smoke config:** `marble/configs/coding_config/coding_config_minimal.yaml`
**Script (loops 100 tasks):** `bash scripts/coding/run_demo.sh`
**Final outputs:**
- `outputs/coding_config/<timestamp>/workspace/solution.py` — generated solution file
- `outputs/coding_config/<timestamp>/development_output.jsonl` — evaluation results
- `outputs/coding_config/<timestamp>/logs/marble.log` — full run log

---

### Database (DB anomaly diagnosis)

```bash
python marble/main.py --config marble/configs/test_config_database/deepseek-v4-flash_E_COMMERCE_FETCH_LARGE_DATA_INSERT_LARGE_DATA.yaml
```

**Requires:** Docker + sudo (PostgreSQL + Prometheus containers)
**Config dir:** `marble/configs/test_config_database/` (100+ YAML files, multiple domains + models)
**Script:** `bash scripts/database/run_simulation.sh`
**Final outputs:**
- `marble/result/result_<model>/<SCENARIO>_RESULT.json` — per-task evaluation result
- Agent logs, slow query analysis, metric alerts printed during run

---

### World (bargaining simulation, 2 agents)

```bash
python marble/main.py --config marble/configs/test_config_world/test_config_world.yaml
```

**Requires:** Bargaining data in `data/bargaining-data/`
**Script:** `bash scripts/world/run.sh`
**Final outputs:**
- `marble/result/discussion_output.jsonl` — negotiation dialogue and outcome

---

### Reasoning (CoT / Reflexion / ReAct variants)

```bash
python marble/main.py --config marble/configs/test_config_reasoning.yaml
python marble/main.py --config marble/configs/test_config_reasoning_cot.yaml
python marble/main.py --config marble/configs/test_config_reasoning_react.yaml
python marble/main.py --config marble/configs/test_config_reasoning_reflexion.yaml
```

**Scripts:** `bash scripts/reasoning/run_reasoning.sh`, `bash scripts/reasoning/run_demo_reasoning.sh`
**Final outputs:**
- `marble/result/discussion_output.jsonl` — reasoning discussion
- `marble/logs/<model_name>/<method>/solution_<id>.py` — per-task solutions

---

### Werewolf (9-agent social deduction)

```bash
source venv/bin/activate && python marble/environments/werewolf_env.py \
  --config_path marble/configs/test_config/werewolf_config/werewolf_config.yaml \
  --rounds 1
```

**Script:** `bash scripts/werewolf/run_simulation.sh`
**Final outputs:**
- `werewolf_log/game_YYYYMMDD_HHMMSS/shared_memory.json` — full game transcript
- `werewolf_log/game_YYYYMMDD_HHMMSS/checkpoint_NightX.json` — per-phase checkpoints
- `werewolf_log/game_YYYYMMDD_HHMMSS/checkpoint_DayX.json` — per-phase checkpoints
- `werewolf_log/game_YYYYMMDD_HHMMSS/N-role-player_log.txt` — individual agent logs
**Note:** Werewolf now uses the same `.env` credentials as every other scenario. The `werewolf_config.yaml` `villager_config`, `werewolf_config`, and `eval_config` blocks no longer contain API keys; optional `model_name` fields are ignored unless they match the active `LLM_SOURCE`.

---

### General Web Simulation

```bash
python marble/main.py --config marble/configs/test_config.yaml
```

**Final outputs:**
- `marble/result/discussion_output.jsonl` — web research results and summary

---

## Utility Scripts

```bash
# Batch update model name across all configs
python scripts/coding/utils/keyword_changing.py \
  --old_model "gpt-4o-mini" --new_model "deepseek-v4-flash"

# Read benchmark categories
python scripts/coding/utils/read_benchmark_category.py

# Update coding config for a specific benchmark ID
python scripts/coding/utils/update_coding_config.py --id <benchmark_id>

# Update reasoning config for a specific benchmark ID
python scripts/reasoning/update_reasoning_config.py --id <benchmark_id> \
  --config <path_to_config.yaml>
```

## Notes

- All scripts and commands are run from the project root (`/Users/saptarshi/workfiles/MARBLE/MARBLE`)
- Use `--rounds N` to control game iterations (werewolf, default: 10)
- The `--config` flag works via argparse prefix matching for `--config_path`
- **API Credentials & Model:** Loaded automatically from `.env` file (uses python-dotenv). To switch providers, change `LLM_SOURCE` in `.env`.
- **Models:** By default each config file leaves `llm`, `model_name`, and `evaluate_llm` empty so `.env` controls the model. You can still override a specific config by setting its `llm` field to a source-compatible model name.

### Output File Write Modes

If you stop a run midway, these files tell you what survives:

| Output File | Write Mode | Partial Data Preserved? |
|---|---|---|
| `outputs/<scenario>/<timestamp>/logs/marble.log` | Append (`"a"`) | ✅ All logged lines so far |
| `outputs/<scenario>/<timestamp>/discussion_output.jsonl` | Append (`"a"`) | ✅ All completed cycles |
| `outputs/<scenario>/<timestamp>/development_output.jsonl` | Append (`"a"`) | ✅ All completed iterations |
| `outputs/<scenario>/<timestamp>/workspace/solution.py` | Overwrite (`"w"`) | ❌ Only most recent solution |
| `outputs/<scenario>/<timestamp>/checkpoints/iter_*/engine.pkl` | Pickle | ✅ Saved at end of each successful iteration |
| `outputs/<scenario>/<timestamp>/checkpoints/iter_*/workspace/` | Copy | ✅ Snapshot of workspace at checkpoint time |
| `outputs/<scenario>/<timestamp>/checkpoints/latest` | Symlink | ✅ Points to last successful iteration |
| `outputs/<scenario>/<timestamp>/checkpoints/failure/` | Copy | ✅ Created on exception; contains failing state |
| `werewolf_log/*/N-role-player_log.txt` | Append (`"a"`) | ✅ All agent actions logged so far |
| `marble/result/result_<model>/*_RESULT.json` | Overwrite (`"w"`) | ❌ Only final result |
| `werewolf_log/*/shared_memory.json` | Overwrite (`"w"`) | ❌ Only latest checkpoint |
| `werewolf_log/*/checkpoint_*.json` | Overwrite (`"w"`) | ❌ Only latest checkpoint |

**Important:** `development_output.jsonl` / `discussion_output.jsonl` are only appended when an iteration completes successfully. If an exception occurs, the partial iteration is *not* written to the JSONL; instead, a failure checkpoint is saved and you can resume from `latest`.

### Quick Smoke Tests

Verify the active LLM source works before running full simulations:

```bash
source venv/bin/activate
set -a && source .env && set +a

# Test with the source selected in .env
python -m unittest tests.test_llm_source_integration -v

# Test the other source explicitly
LLM_SOURCE=rits python -m unittest tests.test_llm_source_integration -v
```

Verify checkpoint/resume mechanics with mocked LLM calls (fast, no provider needed):

```bash
python -m pytest tests/test_checkpoint_resume.py tests/test_pickle_safe_classes.py tests/test_output_manager.py -v
```

### Known Limitations

- **Werewolf speeches fail** with `deepseek-v4-flash`: The speech prompt is too complex (7 required fields, 8 steps) for this model. Night actions and votes work fine. This is a model capability issue, not a bug.
- **Connection errors on long games**: As game state grows, API calls may timeout. This is rate limiting from the provider.
- **Resume does not re-run completed iterations**: If the original run completed iteration *N* successfully, resuming will start iteration *N+1*. Make sure `latest` points to the iteration you want to continue from.
- **Checkpoint size**: `engine.pkl` includes the full Engine state (agents, graph, memory). For very long runs the pickle files can become large; retention policies (e.g., `max_checkpoints`) are not yet implemented.
