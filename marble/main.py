"""
Main entry point for running the Marble simulation engine.
"""

import argparse
import hashlib
import json
import logging
import os
import pickle
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from marble.configs.config import Config
from marble.engine.engine import Engine
from marble.utils.output_manager import backup_config, create_run_paths, setup_logging


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
        required=False,  # optional when resuming
        help="Path to the configuration YAML file.",
    )
    parser.add_argument(
        "--resume_from",
        type=str,
        required=False,
        help="Path to a checkpoint directory to resume from.",
    )
    return parser.parse_args()


def _validate_config_match(config_path: str, checkpoint_metadata: dict) -> None:
    if not config_path:
        return
    with open(config_path, "rb") as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()
    backup_path = checkpoint_metadata.get("config_backup_file")
    if backup_path and Path(backup_path).exists():
        with open(backup_path, "rb") as f:
            backup_hash = hashlib.sha256(f.read()).hexdigest()
        if current_hash != backup_hash:
            logging.warning(
                f"Config mismatch: supplied {config_path} differs from the config used for the checkpoint."
            )


def main() -> None:
    """
    Main function to run the simulation with the specified config file or resume a run.
    """
    args = parse_args()

    if not args.config_path and not args.resume_from:
        logging.error("Either --config_path or --resume_from is required.")
        sys.exit(1)

    if args.resume_from:
        checkpoint_dir = Path(args.resume_from)
        if not checkpoint_dir.exists():
            logging.error(f"Checkpoint directory not found: {checkpoint_dir}")
            sys.exit(1)

        metadata_path = checkpoint_dir / "checkpoint.json"
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        base_dir = Path(metadata["base_dir"])
        config_path = args.config_path or str(base_dir / "config.yaml")
        _validate_config_match(args.config_path, metadata)

        if not os.path.isfile(config_path):
            logging.error(f"Configuration file not found: {config_path}")
            sys.exit(1)

        try:
            config = Config.load(config_path)
        except Exception as e:
            logging.error(f"Error loading configuration from {config_path}: {e}")
            sys.exit(1)

        run_paths = create_run_paths(
            config_path=config_path,
            output_file=getattr(config, "output", {}).get("file_path", "output.jsonl"),
            timestamp=base_dir.name,
            scenario=base_dir.parent.name,
        )
        setup_logging(run_paths.log_file)
        # Re-configure output paths to match the resumed run.
        config.output["file_path"] = str(run_paths.result_file)
        if "workspace_dir" in config.environment:
            config.environment["workspace_dir"] = str(run_paths.workspace_dir)

        with open(checkpoint_dir / "engine.pkl", "rb") as f:
            engine = pickle.load(f)
        engine.restore_from_checkpoint(checkpoint_dir)
        engine.resume()
        return

    # Fresh-run path
    if not os.path.isfile(args.config_path):
        logging.error(f"Configuration file not found: {args.config_path}")
        sys.exit(1)

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

    if "workspace_dir" in config.environment:
        config.environment["workspace_dir"] = str(run_paths.workspace_dir)
    if "file_path" in config.output:
        config.output["file_path"] = str(run_paths.result_file)

    logger = logging.getLogger(__name__)
    logger.info(f"Run artifacts: {run_paths.base_dir}")

    try:
        logging.info(f"Starting engine with configuration: {args.config_path}")
        engine = Engine(config, run_base_dir=run_paths.base_dir)
        engine.start()
    except Exception:
        logging.exception(
            f"An error occurred while running the engine with configuration: {args.config_path}"
        )
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
