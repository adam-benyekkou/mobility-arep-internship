def test_init_sets_cache_and_inputs(fake_transport_zones, monkeypatch):
    import mobility.public_transport_travel_costs as mod
    class TinyGTFS:
        def __init__(self, tz): pass
        def get(self): return "/fake/router"
    monkeypatch.setattr(mod, "GTFS", TinyGTFS)

    pt = mod.PublicTransportTravelCosts(fake_transport_zones)
    assert pt.cache_path.name == "public_transport_travel_costs.parquet"
    assert pt.inputs["transport_zones"] is fake_transport_zones
    assert isinstance(pt.inputs["gtfs"], TinyGTFS)
