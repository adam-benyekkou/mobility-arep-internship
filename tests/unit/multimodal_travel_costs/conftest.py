# tests/unit/multimodal_travel_costs/conftest.py
import os
import pathlib
import pytest
import mobility.asset as asset_mod

@pytest.fixture(autouse=True)
def temp_project_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("MOBILITY_PROJECT_DATA_FOLDER", str(tmp_path))
    return tmp_path

@pytest.fixture(autouse=True)
def patch_asset_init(monkeypatch):
    def fake_init(self, inputs, cache_path):
        self.inputs = inputs
        self.cache_path = cache_path
    monkeypatch.setattr(asset_mod.Asset, "__init__", fake_init)

@pytest.fixture
def project_dir():
    return pathlib.Path(os.environ["MOBILITY_PROJECT_DATA_FOLDER"])

@pytest.fixture
def fake_transport_zones():
    return object()
