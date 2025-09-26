import pandas as pd

def test_get_cached_asset_reads_parquet(monkeypatch, project_dir, fake_transport_zones):
    import mobility.multimodal_travel_costs as mod

    # Minimal fakes so __init__ succeeds
    class FakeTC: 
        def __init__(self, *a, **k): pass
    class FakePT: 
        def __init__(self, *a, **k): pass
    monkeypatch.setattr(mod, "TravelCosts", FakeTC)
    monkeypatch.setattr(mod, "PublicTransportTravelCosts", FakePT)

    multimodal_travel_costs = mod.MultimodalTravelCosts(fake_transport_zones)

    expected = pd.DataFrame({"from":[1], "to":[2], "time":[3.0], "distance":[4.0], "mode":["car"]})
    seen = {}
    def fake_read_parquet(path, *a, **k):
        seen["path"] = str(path)
        return expected
    monkeypatch.setattr(pd, "read_parquet", fake_read_parquet, raising=True)

    dataframe = multimodal_travel_costs.get_cached_asset()
    assert dataframe.equals(expected)
    assert seen["path"] == str(project_dir / "multimodal_travel_costs.parquet")
