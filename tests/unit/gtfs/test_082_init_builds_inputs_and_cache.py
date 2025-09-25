from pathlib import Path
from mobility.gtfs import GTFS

def test_init_builds_inputs_and_cache(project_dir, fake_transport_zones, fake_inputs_hash):
    gtfs_instance = GTFS(fake_transport_zones)

    # Inputs populated
    assert "transport_zones" in gtfs_instance.inputs
    assert gtfs_instance.inputs["transport_zones"] is fake_transport_zones

    # Cache path is hashed and inside project_dir
    assert gtfs_instance.cache_path.parent == project_dir
    assert gtfs_instance.cache_path.name.startswith(f"{fake_inputs_hash}-")
    assert gtfs_instance.cache_path.name.endswith("gtfs_router.rds")

    # Hash path is inside project_dir
    assert gtfs_instance.hash_path.parent == project_dir
    assert gtfs_instance.hash_path.name == f"{fake_inputs_hash}.sha1"

    # Windows-friendly: compare Path objects (not raw strings)
    assert gtfs_instance.cache_path == Path(project_dir) / gtfs_instance.cache_path.name
