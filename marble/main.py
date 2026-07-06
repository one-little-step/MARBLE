"""
Main entry point for running the Marble simulation engine.
"""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from marble.configs.config import Config
from marble.engine.engine import Engine
from marble.utils.output_manager import create_run_paths, setup_logging, backup_config


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Run the Marble simulation engine.")
    parser.add_argument(
        "--config_path",
        type=str,
        required=True,
        help="Path to the configuration YAML file.",
    )
    return parser.parse_args()


def main() -> None:
    """
    Main function to run the simulation with the specified config file.
    """
    args = parse_args()

    # Check if the config file exists
    if not os.path.isfile(args.config_path):
        logging.error(f"Configuration file not found: {args.config_path}")
        sys.exit(1)

    # Load configuration
    try:
        config = Config.load(args.config_path)
    except Exception as e:
        logging.error(f"Error loading configuration from {args.config_path}: {e}")
        sys.exit(1)

    output_file = getattr(config, "output", {}).get("file_path", "output.jsonl")
    run_paths = create_run_paths(
        config_path=args.config_path,
        output_file=output_file,
    )
    setup_logging(run_paths.log_file)
    backup_config(args.config_path, run_paths.config_backup_file)

    # Override workspace and output paths so artifacts land in the run directory.
    if "workspace_dir" in config.environment:
        config.environment["workspace_dir"] = str(run_paths.workspace_dir)
    if "file_path" in config.output:
        config.output["file_path"] = str(run_paths.result_file)

    logger = logging.getLogger(__name__)
    logger.info(f"Run artifacts: {run_paths.base_dir}")

    # Initialize and start the engine
    try:
        logging.info(f"Starting engine with configuration: {args.config_path}")
        engine = Engine(config)
        engine.start()
    except Exception:
        logging.exception(
            f"An error occurred while running the engine with configuration: {args.config_path}"
        )
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
