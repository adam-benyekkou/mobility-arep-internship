# (Name kept from the template; this module uses GeoPackage via GeoPandas, not Parquet.)
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point

from mobility.transport_zones import TransportZones


def test_get_cached_asset_reads_from_expected_path(project_dir, fake_inputs_hash, geopandas_file_stubs):
    # Prepare the stub to return a deterministic GeoDataFrame
    geopandas_file_stubs["read_gdf"] = gpd.GeoDataFrame(
        {
            "transport_zone_id": [0, 1],
            "admin_id": ["11111", "22222"],
            "name": ["CityA", "CityB"],
            "admin_level": ["city", "city"],
            "urban_unit_category": ["A", "B"],
            "geometry": [Point(0, 0), Point(1, 0)],
        },
        geometry="geometry",
        crs="EPSG:4326",
    )

    instance = TransportZones(insee_city_id="11111", method="epci_rings", radius=40)
    result = instance.get_cached_asset()

    # Assert read_file path equals the hashed cache path
    expected_path = Path(project_dir) / f"{fake_inputs_hash}-transport_zones.gpkg"
    assert geopandas_file_stubs["read_path"] == expected_path

    # Spot-check schema and a couple of rows
    assert list(result.columns) == [
        "transport_zone_id",
        "admin_id",
        "name",
        "admin_level",
        "urban_unit_category",
        "geometry",
    ]
    assert result.loc[0, "admin_id"] == "11111"
    assert result.loc[1, "name"] == "CityB"
