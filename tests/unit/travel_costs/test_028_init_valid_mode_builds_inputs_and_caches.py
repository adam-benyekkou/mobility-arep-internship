def test_init_valid_mode_builds_inputs_and_cache(project_dir, fake_transport_zones, patch_osmdata):
    import mobility.travel_costs as mod

    travel_costs = mod.TravelCosts(fake_transport_zones, "car")

    assert travel_costs.inputs["mode"] == "car"
    assert "osm" in travel_costs.inputs
    assert travel_costs.inputs["osm"].cache_path.name == "osm.parquet"

    assert travel_costs.cache_path == project_dir / "dodgr_travel_costs_car.parquet"

    
    assert sorted(patch_osmdata["modes"]) == sorted(["motorcar", "bicycle", "foot"])
    assert patch_osmdata["tz"] is fake_transport_zones
