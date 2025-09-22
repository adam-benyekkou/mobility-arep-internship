def test_dodgr_graph_invokes_rscript_with_expected_args(project_dir, fake_transport_zones, patch_osmdata, patch_rscript):
    import mobility.travel_costs as mod

    travel_costs = mod.TravelCosts(fake_transport_zones, "car")
    osm = travel_costs.inputs["osm"]

    out_path = travel_costs.dodgr_graph(fake_transport_zones, osm, "car")

    assert out_path == project_dir / "dodgr_graph_motorcar.rds"
    assert len(patch_rscript["runs"]) == 1
    args = patch_rscript["runs"][0]

    assert args[0] == str(fake_transport_zones.cache_path)
    assert args[1] == str(osm.cache_path)
    assert args[2] == "motorcar"
    assert args[3] == out_path
