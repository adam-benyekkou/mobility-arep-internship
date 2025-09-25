from pathlib import Path
from mobility.gtfs import GTFS

def test_get_cached_asset_returns_expected_path(project_dir, fake_transport_zones, fake_inputs_hash):
    gtfs_instance = GTFS(fake_transport_zones)
    expected_cached_asset_path = Path(project_dir) / f"{fake_inputs_hash}-gtfs_router.rds"
    assert gtfs_instance.get_cached_asset() == expected_cached_asset_path
