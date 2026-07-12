import os
import tempfile
from pathlib import Path

from marble.utils.output_manager import (
    create_checkpoint_dir,
    create_run_paths,
    copy_workspace,
    resolve_scenario,
    update_latest_checkpoint_symlink,
)


class TestOutputManager:
    def test_creates_timestamped_directories(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.setenv("OUTPUT_ROOT_DIR", tmp)
            paths = create_run_paths(
                config_path="marble/configs/coding_config/coding_config.yaml",
                output_file="development_output.jsonl",
                timestamp="20250706-120000",
            )
            assert paths.base_dir == Path(tmp) / "coding_config" / "20250706-120000"
            assert paths.result_file == paths.base_dir / "development_output.jsonl"
            assert paths.log_file == paths.base_dir / "logs" / "marble.log"
            assert paths.workspace_dir == paths.base_dir / "workspace"
            assert paths.base_dir.exists()
            assert paths.log_file.parent.exists()
            assert paths.workspace_dir.exists()

    def test_resolve_scenario_nested(self):
        assert resolve_scenario("marble/configs/test_config_research/profile_1.yaml") == "test_config_research"

    def test_resolve_scenario_top_level(self):
        assert resolve_scenario("marble/configs/coding_config.yaml") == "coding_config"


def test_create_checkpoint_dir_numbered(tmp_path):
    cp = create_checkpoint_dir(tmp_path, 7)
    assert cp == tmp_path / "checkpoints" / "iter_007"
    assert cp.exists()


def test_latest_checkpoint_symlink(tmp_path):
    cp = create_checkpoint_dir(tmp_path, 3)
    update_latest_checkpoint_symlink(tmp_path, cp)
    latest = tmp_path / "checkpoints" / "latest"
    assert latest.is_symlink()
    assert latest.resolve() == cp


def test_latest_checkpoint_symlink_is_cwd_independent(tmp_path, monkeypatch):
    """Regression test: latest symlink must resolve correctly from any cwd."""
    cp = create_checkpoint_dir(tmp_path, 5)
    update_latest_checkpoint_symlink(tmp_path, cp)
    latest = tmp_path / "checkpoints" / "latest"
    assert latest.is_symlink()
    # The symlink target must be relative to the symlink's own directory.
    target = os.readlink(latest)
    assert not Path(target).is_absolute()
    # Verify it resolves from a different working directory.
    with tempfile.TemporaryDirectory() as other_dir:
        monkeypatch.chdir(other_dir)
        assert latest.exists()
        assert latest.resolve() == cp


def test_copy_workspace(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x = 1")
    dst = tmp_path / "dst"
    copy_workspace(src, dst)
    assert (dst / "a.py").read_text() == "x = 1"
