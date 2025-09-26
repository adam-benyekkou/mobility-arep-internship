import pytest
from mobility.transport_zones import TransportZones

def test_filter_cities_epci_rings_unknown_city_raises(fake_cities_gdf):
    """
    Covers the error branch in filter_cities_epci_rings when no city matches.
    """
    instance = TransportZones(insee_city_id="99999", method="epci_rings", radius=40)
    with pytest.raises(ValueError) as err:
        instance.filter_cities_epci_rings(fake_cities_gdf, "99999")

    # Exact message from module
    assert "No city with id '99999' was found in the admin-express 2023 database." in str(err.value)
