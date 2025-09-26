from types import SimpleNamespace
from pathlib import Path
import pandas as pd

def test_gtfs_router_costs_runs_and_reads(fake_transport_zones, monkeypatch, tmp_path):
    import mobility.public_transport_travel_costs as module

    class FakeGTFS:
        def __init__(self, transport_zones): 
            pass
        def get(self): 
            return "/fake/router"
    monkeypatch.setattr(module, "GTFS", FakeGTFS)

    call_log = {}
    class FakeRScript:
        def __init__(self, script_path):
            call_log["script_path"] = script_path
        def run(self, args):
            call_log["args"] = args
    monkeypatch.setattr(module, "RScript", FakeRScript)

    def resources_files_stub(package_name):
        return SimpleNamespace(joinpath=lambda relative_path: tmp_path / relative_path)
    monkeypatch.setattr(module.resources, "files", resources_files_stub)

    expected_dataframe = pd.DataFrame({"cost": [42]})
    monkeypatch.setattr(pd, "read_parquet", lambda path: expected_dataframe)

    public_transport_travel_costs = module.PublicTransportTravelCosts(fake_transport_zones)
    result_dataframe = public_transport_travel_costs.gtfs_router_costs(
        public_transport_travel_costs.inputs["transport_zones"],
        public_transport_travel_costs.inputs["gtfs"],
    )
    assert result_dataframe.equals(expected_dataframe)

    assert Path(call_log["script_path"]).name == "prepare_public_transport_costs.R"
    transport_zones_path, gtfs_router_path, route_types_path, output_path = call_log["args"]
    assert Path(transport_zones_path).name == "transport_zones.parquet"
    assert gtfs_router_path == "/fake/router"
    assert Path(route_types_path).parts[-3:] == ("data", "gtfs", "gtfs_route_types.xlsx")
    assert Path(output_path).name == "public_transport_travel_costs.parquet"
