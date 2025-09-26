import pandas as pd

def test_prepare_sinks_happy_path(fake_transport_zones):
    import mobility.work_destination_choice_model as mod

    idx = pd.Index(["A1", "A2", "A3"], name="CODGEO")
    jobs = pd.DataFrame({"industry": [100, 200, 300], "services": [40, 60, 90]}, index=idx)

    dummy_costs = pd.DataFrame()
    work_destination_choice_model = mod.WorkDestinationChoiceModel(fake_transport_zones, dummy_costs)

    out = work_destination_choice_model.prepare_sinks(fake_transport_zones, jobs)

    assert list(out.index) == [101, 102, 103]
    assert out.columns.tolist() == ["sink_volume"]
    assert out.loc[101, "sink_volume"] == 140
    assert out.loc[102, "sink_volume"] == 260
    assert out.loc[103, "sink_volume"] == 390
