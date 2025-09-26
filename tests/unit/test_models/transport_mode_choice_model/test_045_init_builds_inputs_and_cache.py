import os

def test_init_builds_inputs_and_cache(monkeypatch, project_dir):
    import mobility.transport_mode_choice_model as mod

    # Don’t run expensive .get() inside __init__
    monkeypatch.setattr(mod.Asset, "get", lambda self: None, raising=True)

    travel_costs = object()
    model = mod.TransportModeChoiceModel(travel_costs, cost_of_time=15.0)

    assert model.inputs["travel_costs"] is travel_costs
    assert model.inputs["cost_of_time"] == 15.0
    assert model.cache_path == project_dir / "deadbeef-modal_choice_model.parquet"
