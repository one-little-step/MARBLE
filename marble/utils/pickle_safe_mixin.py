"""Mixin that makes logger-holding classes safe to pickle."""
import logging
from typing import Any, Dict


class PickleSafeLoggerMixin:
    """
    Drop the logger during pickling and recreate it on unpickling.
    Any subclass that stores ``self.logger`` should inherit this mixin.
    """

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        if "logger" in state:
            del state["logger"]
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__dict__.update(state)
        self.logger = logging.getLogger(self.__class__.__name__)
