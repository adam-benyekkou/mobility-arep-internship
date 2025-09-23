import os
import pandas as pd
import pytest

@pytest.fixture
def project_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("MOBILITY_PROJECT_DATA_FOLDER", str(tmp_path))
    return tmp_path

@pytest.fixture
def fake_transport_zones_asset():
    class FakeTZAsset:
        def __init__(self):
            self._df = pd.DataFrame({"id": [1, 2], "geometry": [None, None]})
        def get(self):
            return self._df
    return FakeTZAsset()

@pytest.fixture
def fake_travel_costs_asset():
    class FakeTCAsset:
        def __init__(self):
            # Minimal costs schema used by the DCM
            self._df = pd.DataFrame({
                "from": [1, 1],
                "to": [2, 2],
                "mode": ["car", "walk"],
                "time": [0.5, 1.0],
                "distance": [10.0, 5.0],
            })
        def get(self):
            return self._df
    return FakeTCAsset()
