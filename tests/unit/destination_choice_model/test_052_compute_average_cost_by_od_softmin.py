import pandas as pd
import numpy as np

def test_compute_average_cost_by_od_softmin(monkeypatch, fake_transport_zones_asset, fake_travel_costs_asset):
    import mobility.destination_choice_model as mod

    monkeypatch.setattr(mod.Asset, "compute_inputs_hash", lambda self: "deadbeef")
    monkeypatch.setattr(mod.Asset, "get", lambda self: None)

    class DummyDCM(mod.DestinationChoiceModel):
        def prepare_sources_and_sinks(self, *a, **k):
            return None, None

    model = DummyDCM("work", fake_transport_zones_asset, fake_travel_costs_asset, cost_of_time=10.0)

    costs = pd.DataFrame({
        "from": [1, 1],
        "to": [2, 2],
        "mode": ["car", "walk"],
        "time": [0.5, 1.0],  # hours
        "distance": [10.0, 5.0],
    })

    out = model.compute_average_cost_by_od(costs)

    # Expected softmin over ct*time with ct=10
    cost_of_time = model.inputs["cost_of_time"]
    util = np.array([-cost_of_time * 0.5, -cost_of_time * 1.0])
    probs = np.exp(util) / np.exp(util).sum()
    expected_cost = (probs * (cost_of_time * np.array([0.5, 1.0]))).sum()

    row = out.loc[(out["from"] == 1) & (out["to"] == 2)].iloc[0]
    assert np.isclose(row["cost"], expected_cost, rtol=1e-9)
