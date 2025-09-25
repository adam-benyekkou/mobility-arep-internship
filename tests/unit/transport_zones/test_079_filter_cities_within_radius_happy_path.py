from mobility.transport_zones import TransportZones

def test_filter_cities_within_radius_happy_path(fake_cities_gdf):
    """
    Covers TransportZones.filter_cities_within_radius happy path.
    NOTE: The geometry is EPSG:4326; buffering with a large 'km' value just
    selects everything deterministically for this synthetic setup.
    """
    instance = TransportZones(insee_city_id="11111", method="radius", radius=40)

    # Use radius=1 km -> buffer(1000) in degree units; in this synthetic setup it effectively includes all points.
    result = instance.filter_cities_within_radius(fake_cities_gdf, "11111", radius=1)

    # All cities should be included by our synthetic geometry + large buffer
    assert set(result["INSEE_COM"]) == {"11111", "22222", "33333"}
    assert set(result["NOM"]) == {"CityA", "CityB", "CityC"}
