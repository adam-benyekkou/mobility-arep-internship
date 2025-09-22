def test_init_sets_cache_and_inputs(fake_transport_zones_asset, temp_project_dir, monkeypatch):
    import mobility.population as mod

    population = mod.Population(fake_transport_zones_asset, sample_size=10)

    assert population.cache_path.name == "population.parquet"
  
    assert population.inputs["transport_zones"] is fake_transport_zones_asset
    assert population.inputs["sample_size"] == 10
