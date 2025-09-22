import pytest
import pandas as pd
import numpy as np

def test_init_builds_inputs_and_cache(monkeypatch, project_dir):
    import mobility.transport_mode_choice_model as mod
    monkeypatch.setattr(mod.Asset, "get", lambda self: None, raising=True)

    model = mod.TransportModeChoiceModel(object(), cost_of_time=10.0)
    assert model.cache_path == project_dir / "deadbeef-modal_choice_model.parquet"

def test_compute_mode_probability_by_od_softmax(monkeypatch):
    import mobility.transport_mode_choice_model as mod
    monkeypatch.setattr(mod.Asset, "get", lambda self: None, raising=True)

    model = mod.TransportModeChoiceModel(object(), cost_of_time=2.0)

    costs = pd.DataFrame({
        "from": [1, 1],
        "to":   [2, 2],
        "mode": ["walk", "car"],
        "time": [1.0, 3.0],
    })

    out = model.compute_mode_probability_by_od(costs, cost_of_time=2.0)

    # utility = -ct * time = -2 * time
    # walk: -2, car: -6
    probs = np.exp([-2.0, -6.0])
    probs = probs / probs.sum()

    row_walk = out[(out["from"] == 1) & (out["to"] == 2) & (out["mode"] == "walk")].iloc[0]
    row_car  = out[(out["from"] == 1) & (out["to"] == 2) & (out["mode"] == "car")].iloc[0]

    assert row_walk["utility"] == -2.0
    assert row_car["utility"] == -6.0
    assert row_walk["prob"] == pytest.approx(probs[0], rel=1e-6)
    assert row_car["prob"]  == pytest.approx(probs[1],  rel=1e-6)
