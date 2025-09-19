import pandas as pd

def test_create_and_get_asset_delegates_and_writes(fake_transport_zones_asset, monkeypatch):
    import mobility.population as module

    population = module.Population(fake_transport_zones_asset, sample_size=5)

    # Fake returns for internal steps
    sample_sizes_df = pd.DataFrame({"admin_id": ["C1"], "n_persons": [2], "transport_zone_id": [101]})
    dummy_census = object()  # anything, it won't be used because we stub get_individuals
    individuals_df = pd.DataFrame({
        "age": [30],
        "socio_pro_category": ["A"],
        "ref_pers_socio_pro_category": ["B"],
        "n_pers_household": [2],
        "n_cars": [0],
        "transport_zone_id": [101],
        "individual_id": ["id-1"],
    })

    population.get_sample_sizes = lambda tz, ss: sample_sizes_df
    population.get_census_data = lambda tz: dummy_census
    population.get_individuals = lambda ss, cd: individuals_df

    written = {}
    def fake_to_parquet(self, path, *a, **k):
        written["path"] = str(path)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet, raising=True)

    result = population.create_and_get_asset()
    assert result.equals(individuals_df)
    assert written["path"].endswith("population.parquet")
