#!/bin/bash
# Run the complete reasoning-pipeline test suite with per-task logging and
# checkpoint/resume support.
#
# Each (method, id) combination gets its own config copy and output scenario, so
# failures are isolated and already-completed tasks are skipped on re-runs.
#
# Environment variables (all optional):
#   OUTPUT_ROOT      - root directory for run outputs (default: outputs_reasoning)
#   LOG_ROOT         - root directory for per-task logs (default: logs_reasoning)
#   RESULT_ROOT      - root directory for aggregated results (default: result_reasoning)
#   START_ID         - first benchmark/task id to run (default: 1)
#   END_ID           - last benchmark/task id to run (default: 10)
#   MAX_RETRIES      - number of resume retries after a failure (default: 2)
#   ATTEMPT_TIMEOUT  - seconds to wait for a single run/resume attempt (default: 600)
#   METHODS          - space-separated list of methods to run (default: reflexion react cot)
#   TASK_IDS         - space-separated list of ids to run (overrides START_ID/END_ID)
#
# Examples:
#   bash scripts/reasoning/run_reasoning.sh
#   OUTPUT_ROOT=/tmp/reasoning_out METHODS=cot TASK_IDS="1 2" bash scripts/reasoning/run_reasoning.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_DIR"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_ROOT="${OUTPUT_ROOT:-outputs_reasoning}"
LOG_ROOT="${LOG_ROOT:-logs_reasoning}"
RESULT_ROOT="${RESULT_ROOT:-result_reasoning}"
START_ID="${START_ID:-1}"
END_ID="${END_ID:-10}"
MAX_RETRIES="${MAX_RETRIES:-2}"
ATTEMPT_TIMEOUT="${ATTEMPT_TIMEOUT:-600}"

mkdir -p "$OUTPUT_ROOT" "$LOG_ROOT" "$RESULT_ROOT"

# Resolve method list
if [ -n "${METHODS:-}" ]; then
    METHOD_NAMES=($METHODS)
else
    METHOD_NAMES=(reflexion react cot)
fi

# Resolve task id list
if [ -n "${TASK_IDS:-}" ]; then
    ID_LIST=($TASK_IDS)
else
    ID_LIST=($(seq "$START_ID" "$END_ID"))
fi

TOTAL_TASKS=$(( ${#METHOD_NAMES[@]} * ${#ID_LIST[@]} ))
COMPLETED=0
FAILED=0
SKIPPED=0
RESUMED=0

SCRIPT_START_TIME=$(date +%s)
MASTER_LOG="$LOG_ROOT/pipeline_$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$(dirname "$MASTER_LOG")"

log() {
    local msg="$1"
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$ts] $msg" | tee -a "$MASTER_LOG"
}

log "==============================================="
log "Reasoning Pipeline Test"
log "Start: $(date)"
log "Project dir: $PROJECT_DIR"
log "Methods: ${METHOD_NAMES[*]}"
log "Task IDs: ${ID_LIST[*]}"
log "Total tasks: $TOTAL_TASKS"
log "Output root: $OUTPUT_ROOT"
log "Log root: $LOG_ROOT"
log "Result root: $RESULT_ROOT"
log "Max retries: $MAX_RETRIES"
log "Attempt timeout: ${ATTEMPT_TIMEOUT}s"
log "==============================================="

# Helper: find the most recent run directory for a scenario
find_latest_run_dir() {
    local scenario="$1"
    local scenario_dir="$OUTPUT_ROOT/$scenario"
    if [ ! -d "$scenario_dir" ]; then
        return
    fi
    # Sort alphabetically; timestamps are YYYYMMDD-HHMMSS so lexicographic = chronological
    find "$scenario_dir" -maxdepth 1 -type d -name '2*' 2>/dev/null | sort | tail -1
}

# Helper: determine whether a run directory represents a completed task
is_task_completed() {
    local run_dir="$1"
    [ -n "$run_dir" ] && [ -d "$run_dir/checkpoints/iter_001" ]
}

# Cross-platform timeout wrapper (macOS lacks GNU timeout; Perl is preinstalled).
# Usage: run_with_timeout <seconds> <command...>
run_with_timeout() {
    local seconds="$1"
    shift
    perl -e 'alarm shift; exec @ARGV' "$seconds" "$@"
}

# Helper: resolve the latest checkpoint path to resume from
resolve_resume_checkpoint() {
    local run_dir="$1"
    local latest_link="$run_dir/checkpoints/latest"
    if [ -L "$latest_link" ]; then
        # readlink returns a target relative to the symlink's directory
        local target
        target=$(readlink "$latest_link")
        echo "$run_dir/checkpoints/$target"
        return
    fi
    # Fallback: if a failure checkpoint exists, resume from it
    if [ -d "$run_dir/checkpoints/failure" ]; then
        echo "$run_dir/checkpoints/failure"
        return
    fi
}

for method_name in "${METHOD_NAMES[@]}"; do
    config_path="marble/configs/test_config_reasoning_${method_name}.yaml"
    if [ ! -f "$config_path" ]; then
        log "[ERROR] Config not found: $config_path"
        FAILED=$((FAILED + ${#ID_LIST[@]}))
        continue
    fi

    method_result_dir="$RESULT_ROOT/$method_name"
    task_config_dir="$method_result_dir/configs"
    mkdir -p "$method_result_dir" "$task_config_dir"

    log ""
    log "=== Method: $method_name ($config_path) ==="

    for id in "${ID_LIST[@]}"; do
        task_name="test_config_reasoning_${method_name}_id_${id}"
        task_log="$LOG_ROOT/${task_name}.log"
        marker="$method_result_dir/completed_${id}.marker"
        failure_marker="$method_result_dir/failed_${id}.marker"

        if [ -f "$marker" ]; then
            log "[SKIP] $task_name already completed."
            SKIPPED=$((SKIPPED + 1))
            continue
        fi

        log ""
        log "-----------------------------------------------"
        log "[START] $task_name at $(date)"
        log "Task log: $task_log"
        log "-----------------------------------------------"

        # Per-task config copy: guarantees a unique scenario/output directory.
        # The copy is named after the method+id so resolve_scenario() produces a
        # readable, deterministic scenario name.
        task_config="$task_config_dir/${task_name}.yaml"
        cp "$config_path" "$task_config"

        rm -f "$failure_marker"

        attempt=0
        success=false
        while [ $attempt -le $MAX_RETRIES ] && [ "$success" = false ]; do
            attempt=$((attempt + 1))
            log "[ATTEMPT $attempt/$((MAX_RETRIES + 1))] $task_name"

            run_dir=$(find_latest_run_dir "$task_name")

            exit_code=0
            if [ "$attempt" -eq 1 ] || [ -z "$run_dir" ]; then
                # First attempt: fresh run
                run_with_timeout "$ATTEMPT_TIMEOUT" \
                    env OUTPUT_ROOT_DIR="$OUTPUT_ROOT" python -m marble.main \
                    --config_path "$task_config" >> "$task_log" 2>&1 || exit_code=$?
            else
                # Retry: resume from the latest checkpoint if available
                resume_cp=$(resolve_resume_checkpoint "$run_dir")
                if [ -n "$resume_cp" ] && [ -d "$resume_cp" ]; then
                    log "[RESUME] $task_name from $resume_cp"
                    echo "[RESUME] attempt $attempt from $resume_cp at $(date)" >> "$task_log"
                    run_with_timeout "$ATTEMPT_TIMEOUT" \
                        env OUTPUT_ROOT_DIR="$OUTPUT_ROOT" python -m marble.main \
                        --config_path "$task_config" \
                        --resume_from "$resume_cp" >> "$task_log" 2>&1 || exit_code=$?
                    RESUMED=$((RESUMED + 1))
                else
                    log "[NO CHECKPOINT] Retrying fresh run for $task_name"
                    run_with_timeout "$ATTEMPT_TIMEOUT" \
                        env OUTPUT_ROOT_DIR="$OUTPUT_ROOT" python -m marble.main \
                        --config_path "$task_config" >> "$task_log" 2>&1 || exit_code=$?
                fi
            fi

            if [ "$exit_code" -eq 142 ] || [ "$exit_code" -eq 14 ] || [ "$exit_code" -eq 271 ]; then
                log "[TIMEOUT] $task_name attempt $attempt exceeded ${ATTEMPT_TIMEOUT}s."
                echo "[TIMEOUT] attempt $attempt exceeded ${ATTEMPT_TIMEOUT}s at $(date)" >> "$task_log"
            fi

            run_dir=$(find_latest_run_dir "$task_name")

            if is_task_completed "$run_dir"; then
                success=true
                cp "$run_dir"/*.jsonl "$method_result_dir/output_${id}.jsonl" 2>/dev/null || true
                touch "$marker"
                log "[DONE] $task_name completed at $(date). Run dir: $run_dir"
                COMPLETED=$((COMPLETED + 1))
            else
                log "[FAIL] $task_name attempt $attempt did not produce iter_001 checkpoint."
                if [ -n "${run_dir:-}" ]; then
                    log "[FAIL] Latest run dir: $run_dir"
                    echo "attempt=$attempt" > "$failure_marker"
                    echo "time=$(date)" >> "$failure_marker"
                    echo "run_dir=$run_dir" >> "$failure_marker"
                fi
            fi
        done

        if [ "$success" = false ]; then
            log "[GIVE UP] $task_name failed after $((MAX_RETRIES + 1)) attempts."
            FAILED=$((FAILED + 1))
        fi
    done

    # Aggregate per-method outputs
    log ""
    log "[AGGREGATE] $method_name"
    if ls "$method_result_dir"/output_*.jsonl >/dev/null 2>&1; then
        cat "$method_result_dir"/output_*.jsonl > "$RESULT_ROOT/${method_name}_output.jsonl"
        log "[AGGREGATE] Wrote $RESULT_ROOT/${method_name}_output.jsonl"
    else
        log "[AGGREGATE] No output files to aggregate for $method_name"
    fi
done

SCRIPT_END_TIME=$(date +%s)
ELAPSED=$((SCRIPT_END_TIME - SCRIPT_START_TIME))
ELAPSED_MIN=$((ELAPSED / 60))

log ""
log "==============================================="
log "Reasoning Pipeline Test Complete"
log "End: $(date)"
log "Elapsed: ${ELAPSED_MIN}m (${ELAPSED}s)"
log "Completed: $COMPLETED / $TOTAL_TASKS"
log "Skipped:   $SKIPPED"
log "Failed:    $FAILED"
log "Resumed:   $RESUMED"
log "Master log: $MASTER_LOG"
log "==============================================="
