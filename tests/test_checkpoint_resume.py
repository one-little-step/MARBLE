import pickle
import tempfile
from pathlib import Path

from marble.configs.config import Config
from marble.engine.engine import Engine
from marble.environments.base_env import BaseEnvironment
from marble.utils.output_manager import update_latest_checkpoint_symlink


def test_base_environment_checkpoint_round_trip():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "workspace"
        workspace.mkdir()
        (workspace / "solution.py").write_text("print('hello')")

        env = BaseEnvironment(name="Test", config={"workspace_dir": str(workspace)})
        checkpoint_dir = Path(tmpdir) / "checkpoint"
        env.save_checkpoint(checkpoint_dir)

        (workspace / "solution.py").write_text("print('goodbye')")
        env.restore_checkpoint(checkpoint_dir)

        assert (workspace / "solution.py").read_text() == "print('hello')"


def test_engine_checkpoint_save_and_restore(tmp_path):
    config = Config.load("marble/configs/coding_config/coding_config_minimal.yaml")
    config.environment["workspace_dir"] = str(tmp_path / "workspace")
    config.output["file_path"] = str(tmp_path / "output.jsonl")

    engine = Engine(config, run_base_dir=tmp_path)
    engine.current_iteration = 2
    engine.evaluator.metrics["planning_score"].append(0.5)

    checkpoint_dir = engine.save_checkpoint("iter_002")
    update_latest_checkpoint_symlink(tmp_path, checkpoint_dir)

    with open(checkpoint_dir / "engine.pkl", "rb") as f:
        restored = pickle.load(f)
    restored.restore_from_checkpoint(checkpoint_dir)

    assert restored.current_iteration == 2
    assert restored.evaluator.metrics["planning_score"] == [0.5]
    assert (tmp_path / "checkpoints" / "latest").is_symlink()
