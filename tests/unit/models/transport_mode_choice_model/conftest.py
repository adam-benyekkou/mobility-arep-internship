# tests/unit/transport_mode_choice_model/conftest.py
import os
import pytest

@pytest.fixture(autouse=True)
def project_env(tmp_path, monkeypatch):
    monkeypatch.setenv("MOBILITY_PROJECT_DATA_FOLDER", str(tmp_path))

@pytest.fixture
def project_dir(tmp_path):
    return tmp_path

# 💡 Key fix: avoid JSON-serializing test doubles during Asset.__init__
@pytest.fixture(autouse=True)
def stub_inputs_hash(monkeypatch):
    import mobility.transport_mode_choice_model as mod
    monkeypatch.setattr(mod.Asset, "compute_inputs_hash", lambda self: "deadbeef", raising=True)

# Optional helper fake if you need one in tests that call .get()
class FakeTravelCosts:
    def __init__(self, df=None): self._df = df
    def get(self): return self._df

@pytest.fixture
def fake_travel_costs():
    return FakeTravelCosts()
