import pandas as pd

def test_create_and_get_asset_calls_router(fake_transport_zones, monkeypatch):
    import mobility.public_transport_travel_costs as module

    class FakeGTFS:
        def __init__(self, transport_zones):
            pass

    monkeypatch.setattr(module, "GTFS", FakeGTFS)

    public_transport_travel_costs = module.PublicTransportTravelCosts(fake_transport_zones)

    expected_dataframe = pd.DataFrame({"ok": [1]})

    def fake_gtfs_router_costs(transport_zones, gtfs):
        return expected_dataframe

    # Isolate this method to verify delegation
    public_transport_travel_costs.gtfs_router_costs = fake_gtfs_router_costs

    result_dataframe = public_transport_travel_costs.create_and_get_asset()
    assert result_dataframe.equals(expected_dataframe)
