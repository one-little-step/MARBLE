#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR" || exit 1

python marble/evaluator/werewolf_evaluator.py \
  --top_level_dir "werewolf_log" \
  --config_path "marble/configs/test_config/werewolf_config/werewolf_config.yaml" \
  --snapshot_folder "placeholder" \
  --base_log_dir "werewolf_log"
