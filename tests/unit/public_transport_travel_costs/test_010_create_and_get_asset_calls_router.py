import pandas as pd

def test_create_and_get_asset_calls_router(fake_transport_zones, monkeypatch):
    import mobility.public_transport_travel_costs as mod
    class TinyGTFS:
        def __init__(self, tz): pass
    monkeypatch.setattr(mod, "GTFS", TinyGTFS)

    pt = mod.PublicTransportTravelCosts(fake_transport_zones)
    df_result = pd.DataFrame({"ok":[1]})
    pt.gtfs_router_costs = lambda tz, gtfs: df_result  # isolate this method
    assert pt.create_and_get_asset().equals(df_result)
