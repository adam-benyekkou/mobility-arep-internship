from types import SimpleNamespace
from pathlib import Path
import pandas as pd

def test_gtfs_router_costs_runs_and_reads(fake_transport_zones, monkeypatch, tmp_path):
    import mobility.public_transport_travel_costs as mod

    class TinyGTFS:
        def __init__(self, tz): pass
        def get(self): return "/fake/router"
    monkeypatch.setattr(mod, "GTFS", TinyGTFS)

    calls = {}
    class TinyRScript:
        def __init__(self, script_path): calls["script_path"] = script_path
        def run(self, args): calls["args"] = args
    monkeypatch.setattr(mod, "RScript", TinyRScript)

    def files_stub(pkg):
        return SimpleNamespace(joinpath=lambda p: tmp_path / p)
    monkeypatch.setattr(mod.resources, "files", files_stub)

    df_expected = pd.DataFrame({"cost":[42]})
    monkeypatch.setattr(pd, "read_parquet", lambda p: df_expected)

    pt = mod.PublicTransportTravelCosts(fake_transport_zones)
    out = pt.gtfs_router_costs(pt.inputs["transport_zones"], pt.inputs["gtfs"])
    assert out.equals(df_expected)

    # Robust path checks
    assert Path(calls["script_path"]).name == "prepare_public_transport_costs.R"
    tz_path, router, route_types, out_path = calls["args"]
    assert Path(tz_path).name == "transport_zones.parquet"
    assert router == "/fake/router"
    assert Path(route_types).parts[-3:] == ("data","gtfs","gtfs_route_types.xlsx")
    assert Path(out_path).name == "public_transport_travel_costs.parquet"
