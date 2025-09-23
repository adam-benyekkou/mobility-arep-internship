import pandas as pd

def test_get_cached_asset_reads_parquet(monkeypatch, project_dir, fake_transport_zones_asset, fake_travel_costs_asset):
    import mobility.destination_choice_model as mod

    monkeypatch.setattr(mod.Asset, "compute_inputs_hash", lambda self: "deadbeef")
    monkeypatch.setattr(mod.Asset, "get", lambda self: None)

    class DummyDCM(mod.DestinationChoiceModel):
        def prepare_sources_and_sinks(self, *a, **k):
            return None, None

    model = DummyDCM("work", fake_transport_zones_asset, fake_travel_costs_asset)

    dataframe = pd.DataFrame({"x": [1]})
    seen = {}
    def fake_read_parquet(path, *a, **k):
        seen["path"] = str(path)
        return dataframe
    monkeypatch.setattr(pd, "read_parquet", fake_read_parquet, raising=True)

    out = model.get_cached_asset()
    assert out.equals(dataframe)
    assert seen["path"].endswith("work_destination_choice_model.parquet")
