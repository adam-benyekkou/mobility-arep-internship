import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box as shapely_box

from mobility.transport_zones import TransportZones


def test_prepare_transport_zones_df_schema_and_values(fake_cities_gdf, fake_urban_units_df):
    # Directly test prepare_transport_zones_df to verify schema and computed fields
    instance = TransportZones(insee_city_id="11111", method="epci_rings", radius=40)

    # filtered cities are just the fake cities here (already minimal)
    transport_zones = instance.prepare_transport_zones_df(fake_cities_gdf.merge(fake_urban_units_df, on="INSEE_COM"))

    # Expected columns and order
    expected_cols = [
        "transport_zone_id",
        "admin_id",
        "name",
        "admin_level",
        "urban_unit_category",
        "geometry",
    ]
    assert list(transport_zones.columns) == expected_cols

    # Values: names, admin_level, ids assigned deterministically 0..n-1
    assert transport_zones["name"].tolist() == ["CityA", "CityB", "CityC"]
    assert (transport_zones["admin_level"] == "city").all()
    assert transport_zones["transport_zone_id"].tolist() == list(range(transport_zones.shape[0]))
