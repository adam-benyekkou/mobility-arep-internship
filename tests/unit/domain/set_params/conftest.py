import sys, types, importlib, mobility
import pytest

@pytest.fixture
def mod():
    # If the package attribute 'set_params' is a function, remove it so it won't shadow the submodule
    if hasattr(mobility, "set_params") and not isinstance(mobility.set_params, types.ModuleType):
        delattr(mobility, "set_params")
    # Ensure a fresh submodule import each test
    sys.modules.pop("mobility.set_params", None)
    return importlib.import_module("mobility.set_params")
