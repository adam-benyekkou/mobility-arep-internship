
import pytest
import pandas as pandas
from mobility.localized_trips import LocalizedTrips

def test_modes_and_distances_when_no_merge_matches(make_fake_trips_asset, patch_choice_models):
    # Trips where localization fails to set both endpoints for one row
    single_trip_dataframe = pandas.DataFrame({
        "trip_id": [1],
        "individual_id": [10],
        "previous_motive": ["1.1"],
        "motive": ["1.1"],     # same motive -> will merge to home twice; keep deterministic behavior
        "mode_id": [7],        # pre-existing mode should be preserved if no new mode found
        "distance": [123.0],   # pre-existing distance should be preserved if no new distance found
    })
    trips_asset = make_fake_trips_asset(trips_dataframe=single_trip_dataframe)
    localized_trips = LocalizedTrips(trips_asset)

    # Empty mode and cost matrices (force "no match")
    empty_mode_matrix = pandas.DataFrame(columns=["from","to","mode","prob"]).set_index(["from","to","mode"])
    empty_cost_matrix = pandas.DataFrame(columns=["from","to","mode","distance"]).set_index(["from","to","mode"])
    population_dataframe = trips_asset.inputs["population"].get()

    output_dataframe = localized_trips.localize_trips(
        single_trip_dataframe,
        population_dataframe,
        empty_cost_matrix,
        empty_mode_matrix,
        pandas.DataFrame({
            "transport_zone_id":[1],
            "to_transport_zone_id":[1],
            "p":[1.0],
        })
    )

    # If no mode/distance found, code falls back to existing columns
    assert int(output_dataframe.loc[0, "mode_id"]) == 7
    assert float(output_dataframe.loc[0, "distance"]) == 123.0
