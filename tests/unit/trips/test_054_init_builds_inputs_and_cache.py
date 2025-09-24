# tests/unit/trips/test_054_init_builds_inputs_and_cache.py
def test_init_builds_inputs_and_cache(project_dir, fake_population, patch_mobility_survey):
    import mobility.trips as mod

    trips = mod.Trips(fake_population)

    # inputs wired
    assert set(trips.inputs.keys()) == {"population", "mobility_survey"}
    assert trips.inputs["population"] is fake_population

    # cache path has the deterministic hash prefix from inputs_hash
    expected = project_dir / f"{trips.inputs_hash}-trips.parquet"
    assert trips.cache_path == expected
