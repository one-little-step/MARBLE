# tests/test_checkpoint_resume_integration.py
import json
import pickle
import tempfile
from pathlib import Path
from unittest.mock import patch

from marble.configs.config import Config
from marble.engine.engine import Engine


def test_interrupt_and_resume_star_coordination():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        config = Config.load("marble/configs/coding_config/coding_config_minimal.yaml")
        config.coordination_mode = "star"
        config.environment["max_iterations"] = 2
        config.environment["workspace_dir"] = str(tmpdir_path / "workspace")
        config.output["file_path"] = str(tmpdir_path / "output.jsonl")

        call_count = {"n": 0}
        original_act = __import__(
            "marble.agent.base_agent", fromlist=["BaseAgent"]
        ).BaseAgent.act

        def failing_act(self, task):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("simulated failure")
            # Keep agent2's revision step fast so the integration test finishes
            # in a reasonable time; the checkpoint/resume pipeline is the focus.
            if self.agent_id == "agent2":
                return ("agent2 revised the solution.", None)
            return original_act(self, task)

        # The coding tool handlers call the LLM to generate/revise code, which
        # makes the integration test slow and flaky. Patch them to write a tiny
        # solution so the test focuses on the checkpoint/resume pipeline while
        # still exercising real BaseAgent.act calls.
        def fast_create_solution(env, task_description: str, model_name: str, file_path: str = "solution.py"):
            full_path = Path(env.workspace_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("def add(a, b): return a + b\n", encoding="utf-8")
            return {
                "success": True,
                "message": f"Solution file created at {full_path}",
                "code": full_path.read_text(encoding="utf-8"),
            }

        def fast_give_advice(env, task_description: str, model_name: str):
            return {"success": True, "message": "Advice given and code revised."}

        def fast_communication_session(
            self, target_agent_id, message, session_id, task, turns=5
        ):
            return {
                "success": True,
                "full_chat_history": [
                    {"from": self.agent_id, "to": target_agent_id, "message": message}
                ],
            }

        # The evaluator prompt templates contain literal JSON braces that
        # confuse str.format(). Patch the evaluator methods so the integration
        # test exercises checkpoint/resume without being blocked by that
        # unrelated formatting bug.
        planning_calls = {"n": 0}

        def patched_evaluate_planning(self, summary, agent_profiles, agent_tasks, results):
            planning_calls["n"] += 1
            if planning_calls["n"] == 2:
                raise RuntimeError("simulated fatal failure after checkpoint")
            self.metrics["planning_score"].append(-1)

        def patched_evaluate_communication(self, task, communications):
            self.metrics["communication_score"].append(-1)

        def patched_evaluate_kpi(self, task, agent_results):
            pass

        with patch(
            "marble.environments.coding_utils.coder.create_solution_handler",
            fast_create_solution,
        ), patch(
            "marble.environments.coding_utils.reviewer.give_advice_and_revise_handler",
            fast_give_advice,
        ), patch(
            "marble.agent.base_agent.BaseAgent._handle_new_communication_session",
            fast_communication_session,
        ), patch(
            "marble.evaluator.evaluator.Evaluator.evaluate_planning",
            patched_evaluate_planning,
        ), patch(
            "marble.evaluator.evaluator.Evaluator.evaluate_communication",
            patched_evaluate_communication,
        ), patch(
            "marble.evaluator.evaluator.Evaluator.evaluate_kpi",
            patched_evaluate_kpi,
        ), patch(
            "marble.agent.base_agent.BaseAgent.act", failing_act
        ):
            # First run: agent2's act raises on the second call, and the second
            # evaluation call raises a fatal error after iter_001 has been
            # checkpointed.
            engine = Engine(config, run_base_dir=tmpdir_path)
            try:
                engine.star_coordinate()
            except RuntimeError:
                pass

            failure_cp = tmpdir_path / "checkpoints" / "failure"
            assert failure_cp.exists()

            # Resume from latest completed checkpoint (iter_001).
            latest = tmpdir_path / "checkpoints" / "latest"
            assert latest.is_symlink()
            assert latest.resolve().name.startswith("iter_")
            assert latest.resolve().exists()

            with open(latest / "engine.pkl", "rb") as f:
                restored = pickle.load(f)
            restored.restore_from_checkpoint(latest)
            restored.resume()

            # Verify output file has iterations (across the failed run and the
            # resumed run, since each run appends a new JSONL record).
            lines = list(open(tmpdir_path / "output.jsonl"))
            all_iterations = []
            for line in lines:
                all_iterations.extend(json.loads(line)["iterations"])
            iteration_numbers = [it["iteration"] for it in all_iterations]
            # With max_iterations=2, the failed run completes iter_001 and fails
            # during iter_002; after resuming we should end with exactly two
            # completed iterations and no duplicates.
            assert len(all_iterations) == 2
            assert sorted(iteration_numbers) == [1, 2]
