import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class RunPaths:
    """Paths for a single simulation run."""

    base_dir: Path
    result_file: Path
    log_file: Path
    workspace_dir: Path
    config_backup_file: Path

    @property
    def log_dir(self) -> Path:
        return self.log_file.parent


def resolve_scenario(config_path: str) -> str:
    """Infer scenario name from config file path."""
    path = Path(config_path)
    # Use the parent directory name if the file is nested, otherwise the stem.
    if path.parent.name in ("configs", "marble"):
        return path.stem
    return path.parent.name


def create_run_paths(
    config_path: str,
    scenario: Optional[str] = None,
    output_file: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> RunPaths:
    """
    Create timestamped directories for a simulation run.

    Args:
        config_path: Path to the config file being run.
        scenario: Optional scenario name override.
        output_file: Optional relative output file path from the config.
        timestamp: Optional timestamp override (defaults to now).

    Returns:
        RunPaths with all resolved directories and files.
    """
    root = Path(os.environ.get("OUTPUT_ROOT_DIR", "outputs"))
    scenario_name = scenario or resolve_scenario(config_path)
    ts = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    base_dir = root / scenario_name / ts
    base_dir.mkdir(parents=True, exist_ok=True)

    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    workspace_dir = base_dir / "workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    if output_file:
        result_file = base_dir / Path(output_file).name
    else:
        result_file = base_dir / "output.jsonl"

    config_backup = base_dir / "config.yaml"

    return RunPaths(
        base_dir=base_dir,
        result_file=result_file,
        log_file=log_dir / "marble.log",
        workspace_dir=workspace_dir,
        config_backup_file=config_backup,
    )


def setup_logging(log_file: Path, level: int = logging.INFO) -> None:
    """Configure root logger to write to both file and stdout."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="a"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def backup_config(config_path: str, dest: Path) -> None:
    """Copy the used config into the run directory for reproducibility."""
    shutil.copy2(config_path, dest)
