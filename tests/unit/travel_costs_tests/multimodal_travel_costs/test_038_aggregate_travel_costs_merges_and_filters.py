import pandas as pd

def test_aggregate_travel_costs_merges_and_filters(monkeypatch, fake_transport_zones):
    import mobility.multimodal_travel_costs as mod

    # Construct object with minimal wiring
    class FakeTravelCost: 
        def __init__(self, *a, **k): pass
    class FakePublicTransport: 
        def __init__(self, *a, **k): pass
    monkeypatch.setattr(mod, "TravelCosts", FakeTravelCost)
    monkeypatch.setattr(mod, "PublicTransportTravelCosts", FakePublicTransport)

    multimodal_travel_costs = mod.MultimodalTravelCosts(fake_transport_zones)

    car = pd.DataFrame({"from":[1], "to":[2], "time":[10.0], "distance":[1.0]})
    walk = pd.DataFrame({"from":[1], "to":[2], "time":[20.0], "distance":[1.0]})
    bicycle = pd.DataFrame({"from":[1], "to":[2], "time":[15.0], "distance":[1.0]})
    # PublicTransport has duplicates for same OD, and one row with NaNs to ensure filtering later
    public_transport_dataframe = pd.DataFrame({
        "from":[1,1,3],
        "to":[2,2,4],
        "time":[12.0, 11.0, None],     # row 0/1 duplicate OD; row 2 has NaN -> filtered
        "distance":[1.0, 1.0, None],
        "mode":["public_transport","public_transport","public_transport"],
    })

    out = multimodal_travel_costs.aggregate_travel_costs(car, walk, bicycle, public_transport_dataframe)

    # 1) Car/Walk/Bicycle got 'mode' set
    assert set(out[out["from"].eq(1) & out["to"].eq(2)]["mode"]) >= {"car","walk","bicycle","public_transport"}

    # 2) PublicTransport, duplicates reduced to the FIRST by time after sorting (11.0 is kept)
    public_transport_kept = out[(out["mode"]=="public_transport") & out["from"].eq(1) & out["to"].eq(2)]
    assert len(public_transport_kept) == 1
    assert public_transport_kept.iloc[0]["time"] == 11.0

    # 3) NaN rows removed
    assert not out["time"].isna().any()
    assert not out["distance"].isna().any()

    # 4) Types cast to int for 'from'/'to'
    assert out["from"].dtype.kind in ("i",) and out["to"].dtype.kind in ("i",)
