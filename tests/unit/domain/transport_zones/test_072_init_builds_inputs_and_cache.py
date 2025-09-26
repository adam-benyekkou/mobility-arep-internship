from pathlib import Path

from mobility.transport_zones import TransportZones


def test_init_sets_inputs_and_hashed_cache_path(project_dir, fake_inputs_hash):
    instance = TransportZones(insee_city_id="11111", method="epci_rings", radius=40)

    # Inputs set as provided
    assert instance.inputs == {"insee_city_id": "11111", "method": "epci_rings", "radius": 40}

    # Cache path is <project_dir>/<hash>-transport_zones.gpkg
    expected = Path(project_dir) / f"{fake_inputs_hash}-transport_zones.gpkg"
    assert instance.cache_path == expected
    # Hash attribute also set
    assert instance.inputs_hash == fake_inputs_hash
