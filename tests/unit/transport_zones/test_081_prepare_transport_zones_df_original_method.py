import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

import mobility.transport_zones as tz_mod
from mobility.transport_zones import TransportZones

def test_prepare_transport_zones_df_original_method(fake_cities_gdf):
    """
    Explicitly executes the ORIGINAL prepare_transport_zones_df method
    (to cover lines 162–174 in mobility/transport_zones.py).
    We call the exported original stored by conftest: tz_mod._original_prepare_transport_zones_df.
    Pass a 'filtered_cities' WITHOUT 'urban_unit_category' so the original merges it in.
    """
    assert hasattr(tz_mod, "_original_prepare_transport_zones_df"), "Original method not exported by conftest."

    instance = TransportZones(insee_city_id="11111", method="epci_rings", radius=40)

    # Use the fake_cities_gdf as 'filtered_cities' (no 'urban_unit_category' yet)
    original_prepare = tz_mod._original_prepare_transport_zones_df
    transport_zones = original_prepare(instance, fake_cities_gdf)

    # Schema checks exactly as the module produces
    expected_cols = ["transport_zone_id", "admin_id", "name", "admin_level", "urban_unit_category", "geometry"]
    assert list(transport_zones.columns) == expected_cols
    assert transport_zones["admin_level"].eq("city").all()
    # IDs are 0..n-1
    assert transport_zones["transport_zone_id"].tolist() == list(range(len(transport_zones)))

    # A couple of representative rows
    by_admin = dict(zip(transport_zones["admin_id"], transport_zones["urban_unit_category"]))
    # The dummy urban units mapping is A/B/C for 11111/22222/33333
    assert by_admin["11111"] == "A"
    assert by_admin["22222"] == "B"
    assert by_admin["33333"] == "C"
