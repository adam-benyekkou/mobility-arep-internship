from pathlib import Path
from mobility.gtfs import GTFS

def test_create_and_get_asset_delegates_and_returns_path(monkeypatch, project_dir, fake_transport_zones, fake_inputs_hash):
    gtfs_instance = GTFS(fake_transport_zones)

    delegate_call_counters = {"get_stops": 0, "download_gtfs_files": 0, "prepare_gtfs_router": 0}
    fake_stops_object = object()
    fake_downloaded_gtfs_files_list = ["a.zip", "b.zip"]
    recorded_arguments = {}

    def fake_get_stops_method(self, transport_zones_argument):
        delegate_call_counters["get_stops"] += 1
        assert transport_zones_argument is fake_transport_zones
        return fake_stops_object

    def fake_download_gtfs_files_method(self, stops_argument):
        delegate_call_counters["download_gtfs_files"] += 1
        assert stops_argument is fake_stops_object
        return fake_downloaded_gtfs_files_list

    def fake_prepare_gtfs_router_method(self, transport_zones_argument, gtfs_files_argument):
        delegate_call_counters["prepare_gtfs_router"] += 1
        assert transport_zones_argument is fake_transport_zones
        assert gtfs_files_argument == fake_downloaded_gtfs_files_list
        recorded_arguments["returned_cache_path"] = str(self.cache_path)
        return self.cache_path

    monkeypatch.setattr(GTFS, "get_stops", fake_get_stops_method, raising=True)
    monkeypatch.setattr(GTFS, "download_gtfs_files", fake_download_gtfs_files_method, raising=True)
    monkeypatch.setattr(GTFS, "prepare_gtfs_router", fake_prepare_gtfs_router_method, raising=True)

    created_asset_path = gtfs_instance.create_and_get_asset()

    assert delegate_call_counters == {
        "get_stops": 1,
        "download_gtfs_files": 1,
        "prepare_gtfs_router": 1,
    }

    expected_cache_path = Path(project_dir) / f"{fake_inputs_hash}-gtfs_router.rds"
    assert created_asset_path == expected_cache_path
    assert recorded_arguments["returned_cache_path"] == str(expected_cache_path)
