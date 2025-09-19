import pandas as pd

def test_get_individuals_samples_and_assigns_ids(monkeypatch):
    import mobility.population as mod

    sample_sizes = pd.DataFrame({
        "admin_id": ["C1", "C2"],
        "transport_zone_id": [101, 102],
        "n_persons": [2, 1],
    })

    cantons_dataframe = pd.DataFrame({
        "INSEE_COM": ["C1", "C2"],
        "INSEE_CAN": ["CAN1", "CAN2"],
    })

   
    census_data = pd.DataFrame(
        {
            "age": [30, 45, 50, 55],
            "socio_pro_category": ["A", "B", "C", "D"],
            "ref_pers_socio_pro_category": ["A", "B", "C", "D"],
            "n_pers_household": [2, 3, 1, 2],
            "n_cars": [0, 1, 1, 0],
            "weight": [0.7, 0.3, 0.6, 0.4],
        },
        index=pd.Index(["CAN1", "CAN1", "CAN2", "CAN2"], name="CANTVILLE"),
    )

   
    counter = {"i": 0}
    def fake_uuid():
        counter["i"] += 1
        return f"id-{counter['i']}"
    monkeypatch.setattr(mod.shortuuid, "uuid", fake_uuid)

    def fake_get_french_cities_boundaries():
        return cantons_dataframe.rename(columns={"INSEE_COM": "INSEE_COM", "INSEE_CAN": "INSEE_CAN"})
    monkeypatch.setattr(mod, "get_french_cities_boundaries", fake_get_french_cities_boundaries)

    population = mod.Population(transport_zones=None, sample_size=0)
    individuals = population.get_individuals(sample_sizes, census_data)

    assert len(individuals) == sample_sizes["n_persons"].sum()
    assert {"age","socio_pro_category","ref_pers_socio_pro_category","n_pers_household","n_cars",
            "transport_zone_id","individual_id"}.issubset(individuals.columns)
    counts = individuals["transport_zone_id"].value_counts().to_dict()
    assert counts[101] == 2 and counts[102] == 1
    assert individuals["individual_id"].iloc[0].startswith("id-")
