# tests/unit/trips/test_061_get_individual_trips_daily_short_trips_path.py
import pandas as pd

def test_get_individual_trips_daily_short_trips_path(monkeypatch, fake_population_asset):
    import mobility.trips as mod

    trips = mod.Trips(fake_population_asset, source="EMP-2019")

    # Make exactly 1 mobile weekday and 1 mobile weekend day
    trips.p_immobility = pd.DataFrame(
        {"immobility_weekday": [259 / 260], "immobility_weekend": [103 / 104]},
        index=pd.Index(["1"], name="csp"),
    )

    # Force exactly ONE travel but with 0 days (n_nights = -1 → -1 + 1 = 0)
    trips.n_travels_db = pd.DataFrame({"n_travels": [1]},
                                      index=pd.Index(["1"], name="csp"))

    trips.travels_db = pd.DataFrame(
        {
            "travel_id": [999],
            "motive": pd.Series(["9"], dtype="string"),  # professional motive
            "n_nights": [-1],                             # yields 0 day
            "destination_city_category": pd.Series(["C"], dtype="string"),
            "pondki": [1.0],
            # The next columns are only used by our test stub below if present
            "csp": ["1"],
            "n_cars": ["0"],
            "city_category": ["C"],
        }
    )

    # Provide a matching long-trips row for travel_id=999 (content won’t matter for our asserts)
    trips.long_trips_db = (
        pd.DataFrame(
            {
                "previous_motive": ["L"],
                "motive": ["L"],
                "mode_id": [0],
                "distance": [0.0],
                "n_other_passengers": [0],
            }
        ).set_index(pd.Index([999], name="travel_id"))
    )

    # Days DB: one weekday + one weekend day matching filters
    trips.days_trip_db = pd.DataFrame(
        {
            "day_id": [101, 102],
            "weekday": [True, False],
            "city_category": ["C", "C"],
            "csp": ["1", "1"],
            "n_cars": ["0", "0"],
            "pondki": [1.0, 1.0],
        }
    )

    # Short-trips DB indexed by day_id (used via .loc[days_id])
    trips.short_trips_db = (
        pd.DataFrame(
            {
                "day_id": [101, 102],
                "previous_motive": ["X", "Y"],
                "motive": ["Z", "W"],
                "mode_id": [1, 2],
                "distance": [3.0, 4.0],
                "n_other_passengers": [0, 1],
            }
        ).set_index("day_id")
    )

    # Robust safe_sample stub: apply filters only if columns exist, then take first n
    def fake_safe_sample(df, n, **kwargs):
        out = df
        def filt(col, val):
            nonlocal out
            if hasattr(out, "columns") and col in out.columns:
                out = out[out[col] == val]
        if "weekday" in kwargs:       filt("weekday", kwargs["weekday"])
        if "csp" in kwargs:           filt("csp", kwargs["csp"])
        if "n_cars" in kwargs:        filt("n_cars", kwargs["n_cars"])
        if "city_category" in kwargs: filt("city_category", kwargs["city_category"])
        n = max(0, int(n))
        return out.iloc[:n].copy()

    monkeypatch.setattr(mod, "safe_sample", fake_safe_sample, raising=True)

    # Act
    out = trips.get_individual_trips(
        csp="1",
        csp_household="1",
        urban_unit_category="C",
        n_pers="2",
        n_cars="0",
        n_years=1,
    )

    # Assert: we still get the two daily short trips
    short = out[out["trip_type"] == "short"].reset_index(drop=True)
    assert len(short) == 2
    assert set(short.columns) >= {
        "trip_id", "previous_motive", "motive", "mode_id",
        "distance", "n_other_passengers", "trip_type"
    }
    assert set(short["previous_motive"]) == {"X", "Y"}
    assert set(short["motive"]) == {"Z", "W"}
