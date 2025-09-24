import pandas as pd

def test_init_sets_parser_and_calls_super(monkeypatch):
    import mobility.work_destination_choice_model as mod
    import mobility.destination_choice_model as base_mod

    # Record calls to DestinationChoiceModel.__init__
    recorded = {}
    orig_init = base_mod.DestinationChoiceModel.__init__

    def rec_init(self, *args, **kwargs):
        recorded["args"] = args
        recorded["kwargs"] = kwargs
        # do NOT call the original; we only record

    monkeypatch.setattr(base_mod.DestinationChoiceModel, "__init__", rec_init, raising=True)

    # Patch parser class so we can assert type
    class _Parser:
        pass

    monkeypatch.setattr(mod, "JobsActivePopulationDistribution", _Parser, raising=True)

    transport_zones = pd.DataFrame({"admin_id": ["A1"], "transport_zone_id": [101], "geometry": [None]})
    travel_costs = pd.DataFrame({"from": [101], "to": [101], "cost": [0.0]})

    work_destination_choice_model = mod.WorkDestinationChoiceModel(
        transport_zones=transport_zones,
        travel_costs=travel_costs,
        cost_of_time=12.5,
        radiation_model_alpha=0.3,
        radiation_model_beta=1.2,
    )

    # Parser instance attached
    assert isinstance(work_destination_choice_model.jobs_active_population, _Parser)

    # Super called with expected positional args
    assert recorded["args"][0] == "work"
    assert recorded["args"][1] is transport_zones
    assert recorded["args"][2] is travel_costs
    assert recorded["args"][3] == 12.5
    assert recorded["args"][4] == 0.3
    assert recorded["args"][5] == 1.2
