import logging
import pickle

from marble.utils.pickle_safe_mixin import PickleSafeLoggerMixin


class DummyClass(PickleSafeLoggerMixin):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.value = 42


def test_pickle_preserves_data_and_recreates_logger():
    obj = DummyClass()
    obj.value = 100
    pickled = pickle.dumps(obj)
    restored = pickle.loads(pickled)
    assert restored.value == 100
    assert restored.logger.name == "DummyClass"
    assert "logger" not in obj.__getstate__()
