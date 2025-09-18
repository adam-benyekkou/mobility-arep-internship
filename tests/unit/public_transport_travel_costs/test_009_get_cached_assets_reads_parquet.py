import pandas as pd

def test_get_cached_asset_reads_parquet(fake_transport_zones, monkeypatch):
    import mobility.public_transport_travel_costs as mod
    class TinyGTFS:  # harmless init
        def __init__(self, tz): pass
    monkeypatch.setattr(mod, "GTFS", TinyGTFS)

    df_expected = pd.DataFrame({"a":[1]})
    monkeypatch.setattr(pd, "read_parquet", lambda p: df_expected)

    pt = mod.PublicTransportTravelCosts(fake_transport_zones)
    out = pt.get_cached_asset()
    assert out.equals(df_expected)
