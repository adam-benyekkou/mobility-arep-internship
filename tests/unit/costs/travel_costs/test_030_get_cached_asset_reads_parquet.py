import pandas as pd
from pathlib import Path

def test_get_cached_asset_reads_parquet(monkeypatch, project_dir, fake_transport_zones, patch_osmdata):
    import mobility.travel_costs as mod

    dataframe = pd.DataFrame({"x": [1]})
    seen = {}

    def fake_read_parquet(p, *a, **k):
        seen["path"] = Path(p)
        return dataframe

    monkeypatch.setattr(pd, "read_parquet", fake_read_parquet, raising=True)

    travel_costs = mod.TravelCosts(fake_transport_zones, "walk")
    out = travel_costs.get_cached_asset()

    # returned object is the mocked df
    assert out is dataframe
    # we read exactly the cache path computed by the class
    assert seen["path"] == travel_costs.cache_path
