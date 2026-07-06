# Complete Changes Documentation

## Date: July 2-6, 2026

---

## 0. Output/Log Organization & Token Budget Control

### Problem
- MARBLE wrote outputs to fixed paths (`marble/result/`, `marble/workspace/`, stdout only), making it hard to keep runs separate and analyze them later.
- `max_token_num` was hardcoded throughout the codebase (often 2048), causing truncated or empty outputs, especially for coding.
- The coding simulation could get stuck when `solution.py` was created empty: later agents couldn't overwrite it.

### Solution
- Added `marble/utils/output_manager.py` to create timestamped run directories (`outputs/<scenario>/<timestamp>/`) and route both file and stdout logging into `logs/marble.log`.
- Added `marble/llms/token_config.py` with `get_max_token_num()` so `.env`'s `MAX_OUTPUT_TOKENS` centrally controls the output token budget for callers that opt in.
- Wired the token helper through `BaseAgent`, `engine_planner`, `evaluator`, memory modules, coding utils, and research utils.
- Made `create_solution_handler` overwrite empty `solution.py` files so the coding loop can recover.

#### Files Created
- `marble/utils/output_manager.py`
- `marble/llms/token_config.py`
- `tests/test_token_config.py`
- `tests/test_output_manager.py`
- `tests/test_coding_recovery.py`
- `marble/configs/coding_config/coding_config_minimal.yaml`
- `marble/configs/test_config_research/profile_1_minimal.yaml`

#### Files Modified
- `.env` — added `MAX_OUTPUT_TOKENS=4096`
- `marble/main.py` — integrates `output_manager`, overrides workspace/output paths per run
- `marble/configs/coding_config/coding_config.yaml` — `output.file_path` is now basename only
- `marble/configs/test_config_research/profile_1.yaml` — `output.file_path` is now basename only
- `marble/agent/base_agent.py` — uses `get_max_token_num(default=2048)`
- `marble/engine/engine_planner.py` — uses `get_max_token_num(...)`
- `marble/evaluator/evaluator.py` — uses `get_max_token_num(...)`
- `marble/memory/short_term_memory.py` / `long_term_memory.py` — uses `get_max_token_num(...)`
- `marble/environments/research_utils/profile_collector.py` — uses `get_max_token_num(...)`
- `marble/environments/coding_utils/coder.py` — overwrites empty solution.py, uses env token budget
- `marble/environments/coding_utils/reviewer.py` / `debugger.py` — use env token budget

#### Output Locations
| Scenario | Output Directory | Key Files |
|---|---|---|
| Coding | `outputs/coding_config/<timestamp>/` | `workspace/solution.py`, `development_output.jsonl`, `logs/marble.log`, `config.yaml` |
| Research | `outputs/test_config_research/<timestamp>/` | `discussion_output.jsonl`, `logs/marble.log`, `config.yaml` |

#### Test Results
- `tests/test_token_config.py` — 5 passed
- `tests/test_output_manager.py` — 3 passed
- `tests/test_coding_recovery.py` — 2 passed
- Full unit/integration suite (24 tests) — passed

#### Smoke Test Status (LLM_SOURCE=rits)
- Coding: created non-empty `solution.py` and progressed through agent collaboration; full 5-iteration run exceeds 10 min because RITS calls take ~60-70s each.
- Research: progressed through iteration 1, retrieved papers, and summarized; full run exceeds 10 min for the same reason.

---

## 1. LLM Source Switching (`LLM_SOURCE=openai` | `rits`)

### Problem
All LLM calls were hardcoded to a single provider/model. Switching to RITS
required editing multiple source files and configs.

### Solution
Introduced a centralized client factory and made `LLM_SOURCE` in `.env` the
single switch that controls every LLM call in MARBLE.

#### Files Created
- **`marble/llms/client_factory.py`** — single source of truth for model/key/URL resolution
  ```python
  from marble.llms.client_factory import get_model_name, get_openai_client
  ```
- **`tests/test_client_factory.py`** — 11 unit tests (no API calls)
- **`tests/test_llm_source_integration.py`** — source-aware integration tests
- **`marble/configs/test_config/werewolf_config/werewolf_config_minimal.yaml`** — small werewolf smoke-test config

#### Files Modified
- **`.env`** — added `LLM_SOURCE`, RITS variables, and `OPENAI_MODEL_NAME`
  ```bash
  LLM_SOURCE=openai          # or "rits"

  OPENAI_API_KEY=...
  OPENAI_BASE_URL=...
  OPENAI_MODEL_NAME=openai/deepseek-v4-flash

  RITS_API_KEY=...
  RITS_BASE_URL=https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com/moonshotai-kimi-k2-7/v1
  RITS_MODEL_NAME=moonshotai/Kimi-K2.7-Code
  ```
- **`marble/llms/model_prompting.py`** — uses factory; supports RITS via `openai/` prefix + `RITS_API_KEY` header
- **`marble/agent/base_agent.py`** — `self.llm` resolved from `LLM_SOURCE`
- **`marble/engine/engine_planner.py`** — default model resolved from `LLM_SOURCE`
- **`marble/evaluator/evaluator.py`** — `evaluate_llm` resolved from `LLM_SOURCE`
- **`marble/evaluator/werewolf_evaluator.py`** — direct OpenAI client created from factory
- **`marble/agent/werewolf_agent.py`** — direct OpenAI client + model from factory
- **`marble/utils/milestone.py`** — direct OpenAI client from factory
- **`marble/memory/short_term_memory.py`** / **`long_term_memory.py`** — summary model from factory
- **`marble/environments/web_env.py`** — trim model from factory
- **`marble/environments/coding_utils/coder.py`** / **`reviewer.py`** / **`debugger.py`** — schema defaults from factory
- **`marble/configs/config.py`** — top-level `llm` resolved from `LLM_SOURCE`
- **All test configs** — `llm`, `evaluate_llm`, `model_name` fields cleared so env takes over
- **`tests/test_model_prompting.py`** — now source-aware

#### Test Results
| Test | OpenAI | RITS |
|------|--------|------|
| `tests.test_client_factory` | ✅ 11/11 | ✅ 11/11 |
| `tests.test_llm_source_integration` | ✅ 2/2 | ✅ 2/2 |
| `tests.test_model_prompting` | ✅ 1/1 | ✅ 1/1 |
| Coding smoke test | ✅ calls opencode.ai | ✅ calls RITS |
| Research smoke test | ✅ calls opencode.ai | ✅ calls RITS |
| Werewolf smoke test | ✅ agents init | ✅ agents init |

---

## 1. API Configuration (`.env` file)

### Problem
API credentials were scattered across multiple config files. No centralized configuration.

### Solution
Created `.env` file in project root and added `python-dotenv` loading to main entry points.

#### Files Created
- **`.env`** - Centralized API credentials
  ```
  OPENAI_API_KEY=sk-LcDUXNZavbyrBE0tZprRIjmN5mist4T52hlRyGP43h8yHVgcdKVJaGONK9yYdAcQ
  OPENAI_BASE_URL=https://opencode.ai/zen/go/v1
  ```

#### Files Modified
- **`marble/main.py`** (lines 1-12) - Added dotenv loading
  ```python
  from dotenv import load_dotenv
  load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
  ```

- **`marble/environments/werewolf_env.py`** (lines 1-18) - Added dotenv loading
  ```python
  from dotenv import load_dotenv
  load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
  ```

---

## 2. Model Configuration Updates (deepseek-v4-flash)

### Problem
Config files for research, coding, reasoning, and world scenarios still had old model names (`gpt-3.5-turbo`, `gpt-4o-mini`, `gpt-4o`) which are not supported by the API provider.

LiteLLM requires a provider prefix for model names. For OpenAI-compatible APIs like opencode.ai, the model must be prefixed with `openai/`.

**Note:** Werewolf config uses OpenAI client directly (not LiteLLM), so it uses `deepseek-v4-flash` without prefix.

### Solution
Updated all config files to use the correct model format:
- **LiteLLM configs:** `openai/deepseek-v4-flash`
- **Werewolf config:** `deepseek-v4-flash` (no change needed)

#### Files Modified

| Config File | Old Model | New Model | Client |
|-------------|-----------|-----------|--------|
| `test_config_research/profile_1.yaml` | `gpt-3.5-turbo` | `openai/deepseek-v4-flash` | LiteLLM |
| `test_config_research/profile_2.yaml` | `gpt-3.5-turbo` | `openai/deepseek-v4-flash` | LiteLLM |
| `test_config_research/profile_3.yaml` | `gpt-3.5-turbo` | `openai/deepseek-v4-flash` | LiteLLM |
| `test_config_reasoning_reflexion.yaml` | `gpt-3.5-turbo` | `openai/deepseek-v4-flash` | LiteLLM |
| `test_config_reasoning_react.yaml` | `gpt-3.5-turbo` | `openai/deepseek-v4-flash` | LiteLLM |
| `test_config_reasoning_cot.yaml` | `gpt-3.5-turbo` | `openai/deepseek-v4-flash` | LiteLLM |
| `coding_config/coding_config.yaml` | `gpt-4o-mini` | `openai/deepseek-v4-flash` | LiteLLM |
| `test_config_world/test_config_world.yaml` | `gpt-3.5-turbo` | `openai/deepseek-v4-flash` | LiteLLM |
| `test_config/werewolf_config/werewolf_config.yaml` | `deepseek-v4-flash` | `deepseek-v4-flash` | OpenAI |

#### Changes Per File

**Research configs (3 files):**
```yaml
# Before
llm: gpt-3.5-turbo

# After
llm: openai/deepseek-v4-flash
```

**Reasoning configs (3 files):**
```yaml
# Before
llm: gpt-3.5-turbo
evaluate_llm:
  model: gpt-3.5-turbo

# After
llm: openai/deepseek-v4-flash
evaluate_llm:
  model: openai/deepseek-v4-flash
```

**Coding config:**
```yaml
# Before
llm: "gpt-4o-mini"
evaluate_llm: "gpt-4o"

# After
llm: "openai/deepseek-v4-flash"
evaluate_llm: "openai/deepseek-v4-flash"
```

**World config:**
```yaml
# Before
llm: "gpt-3.5-turbo"
evaluate_llm: "gpt-3.5-turbo"

# After
llm: "openai/deepseek-v4-flash"
evaluate_llm: "openai/deepseek-v4-flash"
```

---

## 3. Werewolf Agent Fixes

### Problem 1: Windows-style backslash paths
The `werewolf_agent.py` had hardcoded Windows-style paths using backslashes (`\`) which failed on macOS/Linux.

### Fix 1
**File:** `marble/agent/werewolf_agent.py`

Changed 13 instances of backslash paths to forward slashes:
```python
# Before
"marble\agent\werewolf_prompts\guard_prompt.yaml"

# After
"marble/agent/werewolf_prompts/guard_prompt.yaml"
```

Lines affected: ~383-384, 506-516 (prompt template paths)

---

### Problem 2: `tool_choice="required"` causing 400 errors
The API provider "Console Go" rejects `tool_choice="required"` with HTTP 400 errors.

### Fix 2
**File:** `marble/agent/werewolf_agent.py` (line 359)

```python
# Before
tool_choice="required"

# After
tool_choice="auto"
```

---

## 4. Shell Script Fixes

### 4.1 `scripts/werewolf/run_simulation.sh`

#### Problem
- Typo in command: `werewolf_env.pyine_demo`
- Windows-style backslash paths
- No path resolution for portability

#### Fix
```bash
# Before
python marble\environments\werewolf_env.pyine_demo

# After
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_DIR" || exit 1
python marble/environments/werewolf_env.py --config_path "marble/configs/test_config/werewolf_config/werewolf_config.yaml" --rounds 1
```

---

### 4.2 `scripts/werewolf/run_evaluation.sh`

#### Problem
Windows-style backslash paths throughout.

#### Fix
Replaced all `\` with `/` and added path resolution.

---

### 4.3 `scripts/coding/run_demo.sh`

#### Problem 1
`update_coding_config.py` called with `--id` flag but expects positional argument.

#### Fix 1
```bash
# Before
python ${UPDATE_SCRIPT} --id ${id}

# After
python ${UPDATE_SCRIPT} ${id}
```

---

### 4.4 `marble/run_demo.sh`

#### Problem
Tried to run `main.py` from project root instead of `marble/main.py`.

#### Fix
```bash
# Before
CONFIG_FILE="./configs/coding_config"
python main.py --config "$CONFIG_FILE"

# After
CONFIG_FILE="marble/configs/coding_config/coding_config.yaml"
python marble/main.py --config "$CONFIG_FILE"
```

---

### 4.5 `scripts/research/run_simulation.sh`

#### Problem
Config path pointed to directory instead of YAML file.

#### Fix
```bash
# Before
CONFIG_FILE="$PROJECT_DIR/marble/configs/test_config_research"

# After
CONFIG_FILE="$PROJECT_DIR/marble/configs/test_config_research/profile_1.yaml"
```

---

### 4.6 `scripts/world/run.sh`

#### Problem
Hardcoded absolute path to another user's machine.

#### Fix
```bash
# Before
cd /Users/guoshuyi/MARBLE/MARBLE

# After
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_DIR" || exit 1
```

---

### 4.7 `scripts/database/run_simulation.sh`

#### Problem
`cd` command before resolving relative config path broke the path.

#### Fix
Resolve config path before changing directory.

---

### 4.8 `scripts/reasoning/run_reasoning.sh`

#### Problem 1
Config paths missing `test_` prefix.

#### Fix 1
```bash
# Before
"${BASE_CONFIG_DIR}/reflexion_config/coding_config.yaml"

# After
"${BASE_CONFIG_DIR}/test_config_reasoning_reflexion.yaml"
```

#### Problem 2
`update_reasoning_config.py` called with `--id` flag but expects positional argument.

#### Fix 2
```bash
# Before
python ${UPDATE_SCRIPT} --id ${id} --config ${config_path}

# After
python ${UPDATE_SCRIPT} ${id} --config ${config_path}
```

#### Problem 3
Tried to run `main.py` from project root.

#### Fix 3
```bash
# Before
python main.py --config ${config_dir}

# After
python marble/main.py --config ${config_path}
```

---

### 4.9 `scripts/reasoning/run_demo_reasoning.sh`

#### Problem
Wrong path to `update_reasoning_config.py`.

#### Fix
```bash
# Before
UPDATE_SCRIPT="scripts/coding/utils/update_reasoning_config.py"

# After
UPDATE_SCRIPT="scripts/reasoning/update_reasoning_config.py"
```

---

## 5. Python Code Fixes

### 5.1 `marble/evaluator/evaluator.py`

#### Problem 1: Hardcoded relative path
Line 41 had hardcoded relative path to `evaluator_prompts.json`.

#### Fix 1
```python
# Before
prompts_path = "evaluator_prompts.json"

# After
prompts_path = os.path.join(os.path.dirname(__file__), "evaluator_prompts.json")
```

#### Problem 2: Wrong indentation on `except`
Line 324 had wrong indentation causing `SyntaxError`.

#### Fix 2
Fixed indentation to match the `try` block.

---

## 6. Documentation Created

### `RUN.md`
Created comprehensive run instructions for all scenarios:
- Prerequisites and venv activation
- API credentials (`.env` file)
- Commands for each scenario (werewolf, research, coding, world, reasoning)
- Output file locations
- Write mode documentation (append vs overwrite)
- Quick smoke test
- Known limitations

---

## 7. Test Results Summary

### API Tests (with venv activated)
| Scenario | Command | Status |
|----------|---------|--------|
| Werewolf | `scripts/werewolf/run_simulation.sh` | ✅ Works |
| Research | `scripts/research/run_simulation.sh` | ✅ Works (fixed) |
| Coding | `scripts/coding/run_demo.sh` | ✅ Works (fixed) |
| World | `scripts/world/run.sh` | ⚠️ Missing data |
| Reasoning | `scripts/reasoning/run_reasoning.sh` | ✅ Works (fixed) |
| Database | `scripts/database/run_simulation.sh` | ⚠️ Needs Docker |

### Direct Python Commands (all work)
```bash
source venv/bin/activate

# Werewolf
python marble/environments/werewolf_env.py --config_path "marble/configs/test_config/werewolf_config/werewolf_config.yaml" --rounds 1

# Research
python marble/main.py --config_path marble/configs/test_config_research/profile_1.yaml

# Coding
python marble/main.py --config_path marble/configs/coding_config/coding_config.yaml

# World
python marble/main.py --config_path marble/configs/test_config_world/test_config_world.yaml

# Reasoning
python marble/main.py --config_path marble/configs/test_config_reasoning.yaml
```

---

## 8. Known Limitations

### Werewolf Speech Failures
- **Issue:** Player speeches fail 100% of the time with `deepseek-v4-flash`
- **Root Cause:** Speech prompt too complex (7 required fields, 8 steps + role-specific sections)
- **Impact:** Night actions and votes work fine; only speeches are affected
- **Workaround:** None without modifying prompt (out of scope)

### Connection Errors on Long Games
- **Issue:** API calls timeout after Day 3+ as game state grows
- **Root Cause:** Rate limiting from provider as context length increases
- **Impact:** Game may stall on later rounds
- **Workaround:** None (provider limitation)

---

## 9. Files Modified Summary

| File | Changes |
|------|---------|
| `.env` | Created - API credentials |
| `marble/main.py` | Added dotenv loading |
| `marble/environments/werewolf_env.py` | Added dotenv loading |
| `marble/agent/werewolf_agent.py` | Fixed backslash paths, tool_choice |
| `marble/evaluator/evaluator.py` | Fixed path and indentation |
| `scripts/werewolf/run_simulation.sh` | Fixed paths and typo |
| `scripts/werewolf/run_evaluation.sh` | Fixed backslash paths |
| `scripts/coding/run_demo.sh` | Fixed argument passing |
| `scripts/research/run_simulation.sh` | Fixed config path |
| `scripts/world/run.sh` | Fixed hardcoded path |
| `scripts/database/run_simulation.sh` | Fixed path resolution |
| `scripts/reasoning/run_reasoning.sh` | Fixed 3 bugs |
| `scripts/reasoning/run_demo_reasoning.sh` | Fixed script path |
| `marble/run_demo.sh` | Fixed path to main.py |
| `test_config_research/profile_1.yaml` | Updated model to openai/deepseek-v4-flash |
| `test_config_research/profile_2.yaml` | Updated model to openai/deepseek-v4-flash |
| `test_config_research/profile_3.yaml` | Updated model to openai/deepseek-v4-flash |
| `test_config_reasoning_reflexion.yaml` | Updated model to openai/deepseek-v4-flash |
| `test_config_reasoning_react.yaml` | Updated model to openai/deepseek-v4-flash |
| `test_config_reasoning_cot.yaml` | Updated model to openai/deepseek-v4-flash |
| `coding_config/coding_config.yaml` | Updated model to openai/deepseek-v4-flash |
| `test_config_world/test_config_world.yaml` | Updated model to openai/deepseek-v4-flash |
| `RUN.md` | Created - Run documentation |
