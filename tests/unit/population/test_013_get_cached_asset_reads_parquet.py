import pandas as pd

def test_get_cached_asset_reads_parquet(fake_transport_zones_asset, monkeypatch):
    import mobility.population as mod

    expected_dataframe = pd.DataFrame({"a": [1]})
    monkeypatch.setattr(pd, "read_parquet", lambda path: expected_dataframe)

    population = mod.Population(fake_transport_zones_asset, sample_size=5)
    result = population.get_cached_asset()
    assert result.equals(expected_dataframe)
