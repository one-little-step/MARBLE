# tests/test_pickle_safe_classes.py
import pickle

from marble.agent.base_agent import BaseAgent
from marble.configs.config import Config
from marble.environments.base_env import BaseEnvironment
from marble.evaluator.evaluator import Evaluator
from marble.graph.agent_graph import AgentGraph
from marble.memory.base_memory import BaseMemory
from marble.memory.shared_memory import SharedMemory


def test_engine_state_classes_are_pickleable():
    env = BaseEnvironment(name="Test Env", config={"workspace_dir": "/tmp"})
    agent1 = BaseAgent(config={"agent_id": "agent1", "profile": "test"}, env=env)
    agent2 = BaseAgent(config={"agent_id": "agent2", "profile": "test"}, env=env)
    config = Config.load("marble/configs/coding_config/coding_config_minimal.yaml")
    graph = AgentGraph([agent1, agent2], config)
    memory = SharedMemory()
    evaluator = Evaluator(metrics_config={})

    for obj in [env, agent1, agent2, graph, memory, evaluator]:
        pickled = pickle.dumps(obj)
        restored = pickle.loads(pickled)
        assert restored is not obj


def test_restored_agent_msg_box_acts_like_defaultdict():
    env = BaseEnvironment(name="Test Env", config={"workspace_dir": "/tmp"})
    agent = BaseAgent(config={"agent_id": "agent1", "profile": "test"}, env=env)
    agent.msg_box["session_1"]["agent2"].append((agent.FORWARD_TO, "hello"))

    restored = pickle.loads(pickle.dumps(agent))

    # Accessing a missing outer key should yield an empty inner defaultdict.
    assert restored.msg_box["missing_session"]["missing_agent"] == []
    # Existing data should be preserved.
    assert restored.msg_box["session_1"]["agent2"] == [(agent.FORWARD_TO, "hello")]
    # The restored structure should be defaultdict instances, not plain dicts.
    assert isinstance(restored.msg_box, type(agent.msg_box))
    assert isinstance(restored.msg_box["session_1"], type(agent.msg_box["session_1"]))
