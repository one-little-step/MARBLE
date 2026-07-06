import tempfile
from pathlib import Path

from marble.environments.base_env import BaseEnvironment


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
