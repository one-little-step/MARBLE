"""
Configuration management module.
"""

from typing import Any, Dict

import yaml

from marble.llms.client_factory import get_model_name


class Config:
    """
    Configuration class to load and store system configurations.

    This class does not store API keys or other secrets. LLM model selection is
    driven by environment variables (see ``LLM_SOURCE``); any model string in the
    config is only used to select among the env-configured endpoints. Secrets
    should remain in environment variables and never be placed in config files,
    because the Config object is pickled into ``engine.pkl`` checkpoints.
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize the Config with data.

        Args:
            data (Dict[str, Any]): Configuration data.
        """
        self.environment = data.get("environment", {})
        self.relationships = data.get("relationships", [])
        self.agents = data.get("agents", [])
        self.metrics = data.get("metrics", {})
        # LLM model selection is driven by LLM_SOURCE in the environment.
        # The config may optionally specify a model; if it matches the active
        # source it is honored, otherwise the env-configured model wins.
        self.llm = get_model_name(preferred=data.get("llm"))
        self.tools = data.get("tools", {})
        self.logger = data.get("logger", {})
        self.parallel = data.get("parallel", {})
        self.graph = data.get("graph", {})
        self.memory = data.get("memory", {})
        self.engine_planner = data.get("engine_planner", {})
        self.task: Dict[str, Any] = data.get("task", {})
        self.coordination_mode = data.get("coordinate_mode", "centralized")
        self.relationships = data.get("relationships", [])
        self.output = data.get("output", {})

    @staticmethod
    def load(file_path: str) -> "Config":
        """
        Load configuration from a YAML file.

        Args:
            file_path (str): Path to the configuration file.

        Returns:
            Config: An instance of the Config class.

        Raises:
            FileNotFoundError: If the configuration file is not found.
            yaml.YAMLError: If there is an error parsing the YAML file.
        """
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
        return Config(data)
