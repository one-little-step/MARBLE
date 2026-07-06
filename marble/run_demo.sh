#!/bin/bash

# Define the path to the configuration file
CONFIG_FILE="marble/configs/coding_config/coding_config.yaml"

# Execute the simulation engine with the specified configuration
python marble/main.py --config "$CONFIG_FILE"
