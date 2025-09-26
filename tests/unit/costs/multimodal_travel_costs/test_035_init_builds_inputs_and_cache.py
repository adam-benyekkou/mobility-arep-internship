# tests/unit/multimodal_travel_costs/test_040_init_builds_inputs_and_cache.py
def test_init_builds_inputs_and_cache(monkeypatch, project_dir, fake_transport_zones):
    import mobility.multimodal_travel_costs as mod

    created = {"travel_costs": [], "public_transports": []}

    class FakeTC:
        def __init__(self, transport_zones, mode):
            created["travel_costs"].append((transport_zones, mode))

    class FakePT:
        def __init__(self, transport_zones):
            created["public_transports"].append(transport_zones)

    monkeypatch.setattr(mod, "TravelCosts", FakeTC)
    monkeypatch.setattr(mod, "PublicTransportTravelCosts", FakePT)

    multimodal_travel_costs = mod.MultimodalTravelCosts(fake_transport_zones)

    # cache path
    assert multimodal_travel_costs.cache_path == project_dir / "multimodal_travel_costs.parquet"

    # children constructed with expected args
    assert sorted(created["travel_costs"], key=lambda x: x[1]) == [
        (fake_transport_zones, "bicycle"),
        (fake_transport_zones, "car"),
        (fake_transport_zones, "walk"),
    ]
    assert created["public_transports"] == [fake_transport_zones]

    # inputs wired
    assert set(multimodal_travel_costs.inputs.keys()) == {
        "car_travel_costs",
        "walk_travel_costs",
        "bicycle_travel_costs",
        "pub_trans_travel_costs",
    }
