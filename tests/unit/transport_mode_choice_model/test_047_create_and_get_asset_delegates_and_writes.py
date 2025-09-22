import os
import pandas as pd

def test_create_and_get_asset_delegates_and_writes(monkeypatch, project_dir):
    import mobility.transport_mode_choice_model as mod

    monkeypatch.setattr(mod.Asset, "get", lambda self: None, raising=True)

    class FakeTravelCosts:
        def __init__(self, dataframe): self._dataframe = dataframe
        def get(self): return self._dataframe

    input_dataframe = pd.DataFrame({"from": [1], "to": [2], "mode": ["car"], "time": [10.0]})
    travel_costs = FakeTravelCosts(input_dataframe)

    model = mod.TransportModeChoiceModel(travel_costs, cost_of_time=30.0)

    expected = pd.DataFrame({
        "from": [1], "to": [2], "mode": ["car"], "utility": [-300.0], "prob": [1.0]
    })
    # Short-circuit the math; we only care that it’s called and then written
    monkeypatch.setattr(model, "compute_mode_probability_by_od",
                        lambda costs, ct: expected, raising=True)

    written = {}
    def fake_to_parquet(self, path):
        written["path"] = os.fspath(path)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet, raising=True)

    out = model.create_and_get_asset()

    assert out.equals(expected)
    assert written["path"] == os.fspath(project_dir / "deadbeef-modal_choice_model.parquet")
