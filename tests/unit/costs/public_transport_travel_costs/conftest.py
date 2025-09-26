from types import SimpleNamespace
import pytest
import mobility.asset as asset_module  # <-- patch the real base class

@pytest.fixture(autouse=True)
def patch_asset_init(monkeypatch):
    def fake_asset_init(self, inputs, cache_path):
        self.inputs = inputs
        self.cache_path = cache_path
    monkeypatch.setattr(asset_module.Asset, "__init__", fake_asset_init)

@pytest.fixture(autouse=True)
def env_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("MOBILITY_PROJECT_DATA_FOLDER", str(tmp_path))
    return tmp_path

@pytest.fixture
def fake_transport_zones(tmp_path):
    # Your code only needs `.cache_path`
    return SimpleNamespace(cache_path=tmp_path / "transport_zones.parquet")
