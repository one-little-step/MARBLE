import os
import tempfile
from pathlib import Path

from marble.utils.output_manager import create_run_paths, resolve_scenario


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
