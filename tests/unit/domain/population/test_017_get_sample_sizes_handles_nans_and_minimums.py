# tests/unit/population/test_017_get_sample_sizes_handles_nans_and_minimums.py
import pandas as pd

def test_get_sample_sizes_handles_nans_and_minimums(
    fake_transport_zones_asset, transport_zones_dataframe, monkeypatch
):
    import mobility.population as mod

    # Prepare legal population table where one admin_id is missing -> NaN after merge
    legal_population = pd.DataFrame({
        "insee_city_id": ["C1"],          # "C2" is missing on purpose
        "legal_population": [100.0],
    })

    class FakeCityLegalPopulation:
        def get(self):
            return legal_population

    monkeypatch.setattr(mod, "CityLegalPopulation", FakeCityLegalPopulation)

    # --- Workaround for environments where NumPy got reloaded and Series.fillna trips on _NoValueType.
    # Scope it to this test only.
    def safe_series_fillna(self, value=None, inplace: bool = False, *args, **kwargs):
        # simple element-wise replacement without touching NumPy internals
        new_vals = [value if pd.isna(x) else x for x in self.tolist()]
        if inplace:
            self.loc[:] = new_vals
            return None
        return pd.Series(new_vals, index=self.index)

    monkeypatch.setattr(pd.Series, "fillna", safe_series_fillna, raising=False)
    # --------------------------------------------------------------------------

    population = mod.Population(fake_transport_zones_asset, sample_size=10)
    sample_sizes = population.get_sample_sizes(transport_zones_dataframe, sample_size=10)

    # No NaNs after fillna(0)
    assert not sample_sizes["legal_population"].isna().any()

    # n_persons is an integer dtype (allowing pandas' nullable Int64 too)
    assert pd.api.types.is_integer_dtype(sample_sizes["n_persons"])

    # n_persons is at least 1 everywhere
    assert (sample_sizes["n_persons"] >= 1).all()

    # When legal_population was NaN -> it was set to 0 -> still get minimum of 1
    row_c2 = sample_sizes.loc[sample_sizes["admin_id"] == "C2"].iloc[0]
    assert row_c2["n_persons"] == 1
