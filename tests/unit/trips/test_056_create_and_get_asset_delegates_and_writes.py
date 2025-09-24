# tests/unit/trips/test_056_create_and_get_asset_delegates_and_writes.py
import pandas as pd

def test_create_and_get_asset_delegates_and_writes(monkeypatch, fake_population, patch_mobility_survey, parquet_stubs):
    import mobility.trips as mod

    trips = mod.Trips(fake_population)

    expected = pd.DataFrame(
        {
            "trip_id": ["t1", "t2"],
            "previous_motive": ["a", "b"],
            "motive": ["M", "M"],
            "mode_id": [1, 2],
            "distance": [1.0, 2.0],
            "n_other_passengers": [0, 1],
            "individual_id": ["p1", "p1"],
            "trip_type": ["short", "long"],
        }
    )

    # short-circuit the heavy path
    monkeypatch.setattr(mod.Trips, "get_population_trips", lambda self, pop, tz: expected, raising=True)

    result = trips.create_and_get_asset()
    assert result.equals(expected)

    # wrote to the hashed cache file
    assert parquet_stubs["path"] == str(trips.cache_path)
