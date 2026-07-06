#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

CONFIG_FILE="$PROJECT_DIR/marble/configs/test_config_research/profile_1.yaml"

cd "$PROJECT_DIR" || exit 1

mkdir -p result

python marble/main.py --config "$CONFIG_FILE"
