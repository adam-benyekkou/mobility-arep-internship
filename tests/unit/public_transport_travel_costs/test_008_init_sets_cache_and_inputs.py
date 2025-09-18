def test_init_sets_cache_and_inputs(fake_transport_zones, monkeypatch):
    import mobility.public_transport_travel_costs as module

    class FakeGTFS:
        def __init__(self, transport_zones):
            pass
        def get(self):
            return "/fake/router"

    monkeypatch.setattr(module, "GTFS", FakeGTFS)

    public_transport_travel_costs = module.PublicTransportTravelCosts(fake_transport_zones)

    assert public_transport_travel_costs.cache_path.name == "public_transport_travel_costs.parquet"
    assert public_transport_travel_costs.inputs["transport_zones"] is fake_transport_zones
    assert isinstance(public_transport_travel_costs.inputs["gtfs"], FakeGTFS)
