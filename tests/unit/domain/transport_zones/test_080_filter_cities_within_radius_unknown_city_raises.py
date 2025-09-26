import pytest
from mobility.transport_zones import TransportZones

def test_filter_cities_within_radius_unknown_city_raises(fake_cities_gdf):
    """
    Covers the error branch in filter_cities_within_radius when no city matches.
    """
    instance = TransportZones(insee_city_id="99999", method="radius", radius=40)
    with pytest.raises(ValueError) as err:
        instance.filter_cities_within_radius(fake_cities_gdf, "99999", radius=5)
    assert "No city with INSEE code '99999' found." in str(err.value)
