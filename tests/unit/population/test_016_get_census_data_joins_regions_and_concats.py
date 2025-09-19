import pandas as pd
import geopandas as gpd
from types import SimpleNamespace

def test_get_census_data_joins_regions_and_concats(fake_transport_zones_asset, transport_zones_dataframe, monkeypatch, tmp_path):
    import mobility.population as mod

    
    regions_dataframe = pd.DataFrame({"INSEE_REG": ["R1", "R2"], "geometry": [None, None]})

    def fake_sjoin(left, right, how="left", predicate="intersects"):
        dataframe = left.copy()
        dataframe["INSEE_REG"] = ["R1", "R2"][: len(dataframe)]
        return dataframe

    class FakeCensusLocalizedIndividuals:
        def __init__(self, region_code): self.region_code = region_code
        def get(self):
            return pd.DataFrame(
                {
                    "CANTVILLE": [f"{self.region_code}-CAN1", f"{self.region_code}-CAN2"],
                    "age": [25, 40],
                    "socio_pro_category": ["A", "B"],
                    "ref_pers_socio_pro_category": ["A", "B"],
                    "n_pers_household": [2, 3],
                    "n_cars": [0, 1],
                    "weight": [0.6, 0.4],
                }
            )

    monkeypatch.setattr(mod, "get_french_regions_boundaries", lambda: regions_dataframe)
    monkeypatch.setattr(gpd, "sjoin", fake_sjoin)
    monkeypatch.setattr(mod, "CensusLocalizedIndividuals", FakeCensusLocalizedIndividuals)

    population = mod.Population(fake_transport_zones_asset, sample_size=10)
    census_data = population.get_census_data(transport_zones_dataframe)

    assert census_data.index.name == "CANTVILLE"
    assert any(idx.startswith("R1-") for idx in census_data.index)
    assert any(idx.startswith("R2-") for idx in census_data.index)
    assert "weight" in census_data.columns
