import pandas as pd
from pathlib import Path
from mobility.transport_zones import TransportZones

def test_filter_cities_epci_rings_happy_path(fake_cities_gdf, fake_epcis_gdf):
    """
    Covers TransportZones.filter_cities_epci_rings happy path:
    - Finds EPCI of target city
    - Builds first- and second-ring EPCIs via touches + unary_union
    - Filters cities by selected EPCIs (should EXCLUDE the original city's EPCI)
    """
    instance = TransportZones(insee_city_id="11111", method="epci_rings", radius=40)
    result = instance.filter_cities_epci_rings(fake_cities_gdf, "11111")

    # Expect cities from EPCI_B and EPCI_C only (not EPCI_A)
    assert set(result["SIREN_EPCI"]) == {"EPCI_B", "EPCI_C"}
    assert set(result["INSEE_COM"]) == {"22222", "33333"}

    # Keep a couple of schema checks
    assert {"INSEE_COM", "NOM", "SIREN_EPCI", "geometry"} <= set(result.columns)
