import pandas as pd

def test_get_cached_asset_reads_parquet(fake_transport_zones, monkeypatch):
    import mobility.public_transport_travel_costs as mod
    class TinyGTFS: 
        def __init__(self, transport_zones): pass
    monkeypatch.setattr(mod, "GTFS", TinyGTFS)

    expected_dataframe = pd.DataFrame({"a":[1]})
    monkeypatch.setattr(pd, "read_parquet", lambda p: expected_dataframe)

    public_transports_travel_costs = mod.PublicTransportTravelCosts(fake_transport_zones)
    result_dataframe = public_transports_travel_costs.get_cached_asset()
    assert result_dataframe.equals(expected_dataframe)
