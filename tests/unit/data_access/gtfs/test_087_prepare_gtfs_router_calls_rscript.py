# tests/unit/mobility/test_006_prepare_gtfs_router_calls_rscript.py
from pathlib import Path
from mobility.gtfs import GTFS

def test_prepare_gtfs_router_invokes_rscript_run(monkeypatch, project_dir, fake_transport_zones, fake_inputs_hash):
    gtfs = GTFS(fake_transport_zones)

    recorded = {"args": None, "script_path": None}

    class FakeRScript:
        def __init__(self, script_path):
            recorded["script_path"] = str(script_path)
        def run(self, args):
            recorded["args"] = args

    # Patch the RScript class used in the module
    monkeypatch.setattr("mobility.gtfs.RScript", FakeRScript, raising=True)

    # Provide fake GTFS files
    result = gtfs.prepare_gtfs_router(fake_transport_zones, ["x.zip", "y.zip"])

    # The method should return the hashed cache path
    expected_cache = Path(project_dir) / f"{fake_inputs_hash}-gtfs_router.rds"
    assert result == expected_cache

    # It should have joined gtfs files with commas and passed transport_zones.cache_path
    assert recorded["args"][0] == str(fake_transport_zones.cache_path)
    assert recorded["args"][1] == "x.zip,y.zip"
    assert recorded["args"][2] == str(expected_cache)

    # script_path itself is opaque (comes from importlib.resources); just ensure it was provided
    assert recorded["script_path"] is not None
