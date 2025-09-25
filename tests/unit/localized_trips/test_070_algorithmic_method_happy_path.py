import pytest
import pandas as pandas
from mobility.localized_trips import LocalizedTrips

def build_models_for_happy_path():
    # Work destinations (transport_zone_id -> to_transport_zone_id with probability)
    work_destination_dataframe = pandas.DataFrame({
        "transport_zone_id": [1, 2],
        "to_transport_zone_id": [2, 1],
        "p": [1.0, 1.0],
    })
    # Mode choice (full probability for a single mode)
    transport_mode_dataframe = pandas.DataFrame({
        "from": [1, 2],
        "to": [2, 1],
        "mode": [9, 9],
        "prob": [1.0, 1.0],
    }).set_index(["from", "to", "mode"])
    # Travel costs
    travel_costs_dataframe = pandas.DataFrame({
        "from": [1, 2],
        "to": [2, 1],
        "mode": [9, 9],
        "distance": [33.3, 44.4],
    }).set_index(["from", "to", "mode"])
    return work_destination_dataframe, transport_mode_dataframe, travel_costs_dataframe

def test_localize_trips_happy_path(make_fake_trips_asset, patch_choice_models):
    # Build LocalizedTrips just to access instance methods (init wiring tested elsewhere)
    trips_asset = make_fake_trips_asset()
    localized_trips = LocalizedTrips(trips_asset)

    trips_dataframe = trips_asset.get()
    population_dataframe = trips_asset.inputs["population"].get()
    work_destination_dataframe, transport_mode_dataframe, travel_costs_dataframe = build_models_for_happy_path()

    output_dataframe = localized_trips.localize_trips(
        trips_dataframe,
        population_dataframe,
        travel_costs_dataframe,
        transport_mode_dataframe,
        work_destination_dataframe,
    )

    # Deterministic sample fixture ensures a single choice per group
    # Check a few invariants
    assert "from_transport_zone_id" in output_dataframe.columns
    assert "to_transport_zone_id" in output_dataframe.columns
    assert "mode_id" in output_dataframe.columns
    assert "distance" in output_dataframe.columns

    # With our 1.0 probabilities, routes map 1->2 and 2->1 & mode 9 picked, distances replaced
    row_trip_1 = output_dataframe.loc[output_dataframe["trip_id"] == 1].iloc[0]
    assert int(row_trip_1["from_transport_zone_id"]) == 1
    assert int(row_trip_1["to_transport_zone_id"]) == 2
    assert int(row_trip_1["mode_id"]) == 9
    assert pytest.approx(float(row_trip_1["distance"]), rel=1e-9) == 33.3
