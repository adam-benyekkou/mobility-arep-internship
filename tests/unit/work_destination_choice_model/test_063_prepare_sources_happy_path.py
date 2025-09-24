import pandas as pd

def test_prepare_sources_happy_path(fake_transport_zones):
    import mobility.work_destination_choice_model as mod

    # Build active population indexed by CODGEO with two columns to exercise sum(axis=1)
    idx = pd.Index(["A1", "A2", "A3"], name="CODGEO")
    active = pd.DataFrame({"men": [10, 20, 30], "women": [5, 7, 9]}, index=idx)

    # Minimal model (base stub from conftest is fine)
    dummy_costs = pd.DataFrame()
    work_destination_choice_model = mod.WorkDestinationChoiceModel(fake_transport_zones, dummy_costs)

    out = work_destination_choice_model.prepare_sources(fake_transport_zones, active)

    # Expect sum per CODGEO -> merge to transport_zone_id -> index by transport_zone_id
    # A1: 10+5=15, A2: 27, A3: 39
    assert list(out.index) == [101, 102, 103]
    assert out.columns.tolist() == ["source_volume"]
    assert out.loc[101, "source_volume"] == 15
    assert out.loc[102, "source_volume"] == 27
    assert out.loc[103, "source_volume"] == 39
