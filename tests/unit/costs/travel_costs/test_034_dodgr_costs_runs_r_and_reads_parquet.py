import pandas as pd
from pathlib import Path

def test_dodgr_costs_runs_r_and_reads_parquet(monkeypatch, project_dir, fake_transport_zones, patch_osmdata):
    import mobility.travel_costs as mod

    # Make RScript a harmless spy
    called = {}
    class FakeRScript:
        def __init__(self, script_path):
            called["script_path"] = script_path  # just record it
        def run(self, args):
            called["run_args"] = args

    monkeypatch.setattr(mod, "RScript", FakeRScript, raising=True)

    # Stub out parquet read to return a known DF and capture the path used
    dataframe = pd.DataFrame({"cost": [1, 2, 3]})
    seen = {}
    def fake_read_parquet(p, *a, **k):
        seen["path"] = Path(p)
        return dataframe
    monkeypatch.setattr(pd, "read_parquet", fake_read_parquet, raising=True)

    # Build the SUT (constructor will use patched OSMData and env from project_dir)
    travel_costs = mod.TravelCosts(fake_transport_zones, "car")

    # Call the method under test
    out = travel_costs.dodgr_costs(fake_transport_zones, "graph.rds")

    # It should return the dataframe read from parquet
    assert out is dataframe

    # RScript.run should be called with transport_zones.cache_path, the graph, and the travel_costs.cache_path
    assert called["run_args"] == [str(fake_transport_zones.cache_path), "graph.rds", str(travel_costs.cache_path)]

    # And read_parquet should read exactly the computed cache file
    assert seen["path"] == travel_costs.cache_path
