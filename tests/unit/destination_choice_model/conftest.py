import sys
import types
import os
import pandas as pd
import pytest

# Always set the project data folder for every test in this package
@pytest.fixture(autouse=True)
def set_project_env(tmp_path, monkeypatch):
    monkeypatch.setenv("MOBILITY_PROJECT_DATA_FOLDER", str(tmp_path))

# Ensure rich.progress.Progress exists as a no-op
@pytest.fixture(scope="session", autouse=True)
def ensure_rich_progress():
    if "rich" not in sys.modules:
        sys.modules["rich"] = types.ModuleType("rich")
    if "rich.progress" not in sys.modules:
        sys.modules["rich.progress"] = types.ModuleType("rich.progress")

    class _NoOpProgress:
        def __init__(self, *_, **__): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False
        def add_task(self, *_, **__): return 0
        def update(self, *_, **__): return None
        def advance(self, *_, **__): return None

    sys.modules["rich.progress"].Progress = _NoOpProgress

@pytest.fixture
def project_dir(tmp_path):
    return tmp_path

@pytest.fixture
def fake_transport_zones_asset():
    class FakeTZAsset:
        def __init__(self):
            self._dataframe = pd.DataFrame({"id": [1, 2], "geometry": [None, None]})
        def get(self):
            return self._dataframe
    return FakeTZAsset()

@pytest.fixture
def fake_travel_costs_asset():
    class FakeTCAsset:
        def __init__(self):
            self._dataframe = pd.DataFrame({
                "from": [1, 1],
                "to": [2, 2],
                "mode": ["car", "walk"],
                "time": [0.5, 1.0],
                "distance": [10.0, 5.0],
            })
        def get(self):
            return self._dataframe
    return FakeTCAsset()
