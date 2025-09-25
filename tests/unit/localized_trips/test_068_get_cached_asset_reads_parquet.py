# tests/unit/mobility/localized_trips/test_002_get_cached_asset_reads_parquet.py
import pandas as pandas
from mobility.localized_trips import LocalizedTrips

def test_get_cached_asset_reads_parquet(
    make_fake_trips_asset,
    patch_choice_models,
    parquet_stubs,
    project_dir,
):
    trips_asset = make_fake_trips_asset()
    localized_trips = LocalizedTrips(trips_asset)

    expected_dataframe = pandas.DataFrame({"trip_id":[1], "mode_id":[1]})
    parquet_capture = parquet_stubs.stub_read(return_dataframe=expected_dataframe)

    output_dataframe = localized_trips.get_cached_asset()

    # read_parquet called once with exact hashed cache path
    assert parquet_capture.read_calls == [localized_trips.cache_path]
    # returned dataframe is the stubbed one
    pandas.testing.assert_frame_equal(
        output_dataframe.reset_index(drop=True),
        expected_dataframe.reset_index(drop=True),
    )
