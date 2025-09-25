import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box as shapely_box
import pytest

from mobility.transport_zones import TransportZones


def test_invalid_method_raises(monkeypatch):
    # Minimal cities to pass get_french_cities_boundaries
    monkeypatch.setattr(
        "mobility.parsers.admin_boundaries.get_french_cities_boundaries",
        lambda: gpd.GeoDataFrame({"INSEE_COM": [], "NOM": [], "SIREN_EPCI": [], "geometry": []}, geometry="geometry", crs="EPSG:4326"),
        raising=True,
    )
    instance = TransportZones(insee_city_id="11111", method="not_a_method", radius=40)
    with pytest.raises(ValueError) as err:
        instance.create_and_get_asset()
    assert "Method should be one of : epci_rings, radius." in str(err.value)


def test_filter_cities_epci_rings_missing_city_raises(fake_epcis_gdf, monkeypatch):
    # Cities without the target INSEE
    cities = gpd.GeoDataFrame(
        {
            "INSEE_COM": ["22222"],
            "NOM": ["OtherCity"],
            "SIREN_EPCI": ["EPCI_B"],
            "geometry": [Point(1.25, 0.25)],
        },
        geometry="geometry",
        crs="EPSG:4326",
    )

    instance = TransportZones(insee_city_id="99999", method="epci_rings", radius=40)
    monkeypatch.setattr("mobility.parsers.admin_boundaries.get_french_epci_boundaries", lambda: fake_epcis_gdf, raising=True)

    with pytest.raises(ValueError) as err:
        instance.filter_cities_epci_rings(cities, "99999")
    assert "No city with id '99999' was found" in str(err.value)


def test_filter_cities_within_radius_missing_city_raises():
    cities = gpd.GeoDataFrame(
        {
            "INSEE_COM": ["22222"],
            "NOM": ["OtherCity"],
            "SIREN_EPCI": ["EPCI_B"],
            "geometry": [Point(1.25, 0.25)],
        },
        geometry="geometry",
        crs="EPSG:4326",
    )

    instance = TransportZones(insee_city_id="11111", method="radius", radius=40)
    with pytest.raises(ValueError) as err:
        instance.filter_cities_within_radius(cities, "11111", 40)
    assert "No city with INSEE code '11111' found." in str(err.value)
