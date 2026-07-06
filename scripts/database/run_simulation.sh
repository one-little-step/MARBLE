#!/bin/bash

# Define the path to the configuration file
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

CONFIG_FILE="$PROJECT_DIR/marble/configs/test_config_database/gpt-3.5-turbo_E_COMMERCE_FETCH_LARGE_DATA_INSERT_LARGE_DATA.yaml"

cd "$PROJECT_DIR" || exit 1

mkdir -p result

python marble/main.py --config "$CONFIG_FILE"
