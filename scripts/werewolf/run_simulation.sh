#!/bin/bash


SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR" || exit 1

mkdir -p result

python marble/environments/werewolf_env.py --config_path marble/configs/test_config/werewolf_config/werewolf_config.yaml
