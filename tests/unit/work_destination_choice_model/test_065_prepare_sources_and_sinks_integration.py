import pandas as pd

def test_prepare_sources_and_sinks_uses_parser(monkeypatch, fake_transport_zones):
    import mobility.work_destination_choice_model as mod

    # Create deterministic tiny frames consistent with transport_zones
    idx = pd.Index(["A1", "A2", "A3"], name="CODGEO")
    active = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}, index=idx)  # sums: 5,7,9
    jobs   = pd.DataFrame({"x": [10, 20, 30], "y": [1,  2,  3]}, index=idx)  # sums: 11,22,33

    class _Parser:
        def get(self):
            return active, jobs

    monkeypatch.setattr(mod, "JobsActivePopulationDistribution", _Parser, raising=True)

    work_destination_choice_model = mod.WorkDestinationChoiceModel(fake_transport_zones, pd.DataFrame())
    sources, sinks = work_destination_choice_model.prepare_sources_and_sinks(fake_transport_zones)

    # Verify both paths
    assert sources.index.tolist() == [101, 102, 103]
    assert sinks.index.tolist() == [101, 102, 103]
    assert sources["source_volume"].tolist() == [5, 7, 9]
    assert sinks["sink_volume"].tolist() == [11, 22, 33]
