import pandas as pd
import numpy as np

def test_create_and_get_asset_delegates_and_writes(monkeypatch, project_dir, fake_transport_zones_asset, fake_travel_costs_asset):
    import mobility.destination_choice_model as mod

    # Keep Asset lightweight for unit test
    monkeypatch.setattr(mod.Asset, "compute_inputs_hash", lambda self: "deadbeef")
    monkeypatch.setattr(mod.Asset, "get", lambda self: None)

    # Match the real call sites: iter_radiation_model(..., costs=..., alpha=..., beta=...)
    def fake_iter_radiation_model(sources, sinks, costs, alpha, beta):
        multipoint_index = pd.MultiIndex.from_tuples([(1, 2), (2, 1)], names=["from", "to"])
        flows = pd.Series([100.0, 50.0], index=multipoint_index)
        return flows, None, None

    monkeypatch.setattr(mod.radiation_model, "iter_radiation_model", fake_iter_radiation_model)

    # Capture parquet write path
    written = {}
    def fake_to_parquet(self, path, *a, **k):
        written["path"] = str(path)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet, raising=True)

    class DummyDCM(mod.DestinationChoiceModel):
        def prepare_sources_and_sinks(self, transport_zones):
            return {"from": [1]}, {"to": [2]}

    model = DummyDCM("work", fake_transport_zones_asset, fake_travel_costs_asset, cost_of_time=20.0)

    result = model.create_and_get_asset()
    assert {"from", "to", "prob"} <= set(result.columns)
    assert np.isclose(result.loc[result["from"] == 1, "prob"].sum(), 1.0)
    assert written["path"].endswith("work_destination_choice_model.parquet")
