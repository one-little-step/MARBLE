#!/bin/bash

# Define the path to the configuration file
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Use RITS API (Kimi-K2.7-Code) for this database simulation run.
export LLM_SOURCE=rits

CONFIG_FILE="$PROJECT_DIR/marble/configs/test_config_database/gpt-3.5-turbo_E_COMMERCE_FETCH_LARGE_DATA_INSERT_LARGE_DATA.yaml"

cd "$PROJECT_DIR" || exit 1

mkdir -p result

# Generate a timestamp and export it so main.py uses the same run directory.
export OUTPUT_TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SCENARIO_NAME="test_config_database"
TERMINAL_LOG="outputs/$SCENARIO_NAME/$OUTPUT_TIMESTAMP/terminal_output.log"

# Ensure the run directory exists before tee tries to write there.
mkdir -p "outputs/$SCENARIO_NAME/$OUTPUT_TIMESTAMP"

# Run the simulation and capture all terminal output to a file as well as stdout.
python marble/main.py --config "$CONFIG_FILE" 2>&1 | tee "$TERMINAL_LOG"
