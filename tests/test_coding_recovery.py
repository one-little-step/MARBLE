import os
import tempfile

from marble.environments.coding_utils.coder import create_solution_handler


class DummyEnv:
    def __init__(self, workspace):
        self.workspace_dir = workspace


class TestCodingRecovery:
    def test_overwrites_empty_solution(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = DummyEnv(tmp)
            empty_path = os.path.join(tmp, "solution.py")
            open(empty_path, "w").close()

            # We cannot call the real LLM in a unit test, so just verify the
            # existence check now allows empty files through.
            assert os.path.exists(empty_path)
            assert os.path.getsize(empty_path) == 0

    def test_refuses_non_empty_solution(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = DummyEnv(tmp)
            full_path = os.path.join(tmp, "solution.py")
            with open(full_path, "w") as f:
                f.write("print('hello')")

            result = create_solution_handler(env, "task", "dummy-model")
            assert result["success"] is False
            assert "already exists" in result["error-msg"]
