import pandas as pd

def test_create_and_get_asset_delegates_and_writes(monkeypatch, project_dir, fake_transport_zones):
    import mobility.multimodal_travel_costs as mod

    # Prepare children that expose .get() with distinct frames
    class Car: 
        def get(self): return pd.DataFrame({"from":[1], "to":[2], "time":[10.0], "distance":[1.0], "mode":["car"]})
    class Walk:
        def get(self): return pd.DataFrame({"from":[1], "to":[2], "time":[20.0], "distance":[1.0], "mode":["walk"]})
    class Bike:
        def get(self): return pd.DataFrame({"from":[1], "to":[2], "time":[15.0], "distance":[1.0], "mode":["bicycle"]})
    class PublicTransport:
        def get(self): return pd.DataFrame({"from":[1,1], "to":[2,2], "time":[12.0, 11.0], "distance":[1.0,1.0], "mode":["public_transport","public_transport"]})

    # Replace child classes with fakes
    monkeypatch.setattr(mod, "TravelCosts", lambda tz, mode: {"car": Car, "walk": Walk, "bicycle": Bike}[mode]())
    monkeypatch.setattr(mod, "PublicTransportTravelCosts", lambda tz: PublicTransport())

    multimodal_travel_costs = mod.MultimodalTravelCosts(fake_transport_zones)

    # Spy on aggregate to ensure delegation
    called = {}
    def fake_aggregate(self, car, walk, bicycle, pub_trans):
        called["car"], called["walk"], called["bicycle"], called["public_transport"] = car, walk, bicycle, pub_trans
        return pd.DataFrame({"ok":[1]})
    monkeypatch.setattr(mod.MultimodalTravelCosts, "aggregate_travel_costs", fake_aggregate, raising=True)

    # Capture write path
    written = {}
    def fake_to_parquet(self, path, *a, **k):
        written["path"] = str(path)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet, raising=True)

    out = multimodal_travel_costs.create_and_get_asset()

    assert "ok" in out.columns
    assert written["path"] == str(project_dir / "multimodal_travel_costs.parquet")
    # All four child frames were passed through to aggregate
    assert isinstance(called["car"], pd.DataFrame)
    assert isinstance(called["walk"], pd.DataFrame)
    assert isinstance(called["bicycle"], pd.DataFrame)
    assert isinstance(called["public_transport"], pd.DataFrame)
