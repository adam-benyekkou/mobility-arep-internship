import pandas as pandas
from mobility.localized_trips import LocalizedTrips

def test_create_and_get_delegates_and_writes(
    make_fake_trips_asset,
    patch_choice_models,
    parquet_stubs,
    fake_inputs_hash,
):
    # Trips with minimal required columns
    initial_trips_dataframe = pandas.DataFrame({
        "trip_id": [1, 2],
        "individual_id": [10, 20],
        "previous_motive": ["1.1", "9.91"],
        "motive": ["9.91", "1.1"],
        "mode_id": [0, 0],
        "distance": [0.0, 0.0],
    })
    trips_asset = make_fake_trips_asset(trips_dataframe=initial_trips_dataframe)
    localized_trips = LocalizedTrips(trips_asset)

    # Parquet write stub
    parquet_capture = parquet_stubs.stub_write()

    output_dataframe = localized_trips.create_and_get_asset()

    # Should have written exactly once to the hashed cache path, with hash prefix
    assert parquet_capture.write_calls == [localized_trips.cache_path]
    assert localized_trips.cache_path.name.startswith(f"{fake_inputs_hash}-")

    # Result basics: columns added / preserved
    expected_columns = set(initial_trips_dataframe.columns) | {
        "from_transport_zone_id",
        "to_transport_zone_id",
    }
    assert expected_columns.issubset(set(output_dataframe.columns))

    # Representative invariants: trip_ids preserved and shape is consistent
    assert sorted(output_dataframe["trip_id"].tolist()) == [1, 2]
