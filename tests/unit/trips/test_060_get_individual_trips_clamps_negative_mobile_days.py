import pandas as pd
import numpy as np


def _patch_numpy_core_methods(monkeypatch):
    """Work around NumPy sentinel `_NoValue` causing TypeErrors in some pandas ops."""
    import numpy as _np
    from numpy.core import _methods as _nm  # private but stable enough for testing

    def _wrap_sum(a, axis=None, dtype=None, out=None, keepdims=False,
                  initial=_nm._NoValue, where=True):
        if initial is _nm._NoValue:
            return _np.sum(a, axis=axis, dtype=dtype, out=out,
                           keepdims=keepdims, where=where)
        return _np.sum(a, axis=axis, dtype=dtype, out=out,
                       keepdims=keepdims, initial=initial, where=where)

    def _wrap_amax(a, axis=None, out=None, keepdims=False,
                   initial=_nm._NoValue, where=True):
        if initial is _nm._NoValue:
            return _np.amax(a, axis=axis, out=out, keepdims=keepdims, where=where)
        return _np.amax(a, axis=axis, out=out, keepdims=keepdims,
                        initial=initial, where=where)

    monkeypatch.setattr(_nm, "_sum", _wrap_sum, raising=False)
    monkeypatch.setattr(_nm, "_amax", _wrap_amax, raising=False)


def _seed_trips_dbs(trips):
    """Attach survey tables, then make travels absurdly long to force clamping."""
    trips.p_immobility = pd.DataFrame(
        {"immobility_weekday": [0.1], "immobility_weekend": [0.1]},
        index=pd.Index(["1"], name="csp"),
    )

    trips.n_travels_db = pd.DataFrame(
        {"n_travels": [2]},
        index=pd.Index(["1"], name="csp"),
    )

    # Very long travels to make (52*5 - pro_days) or (52*2 - perso_days) go negative
    trips.travels_db = pd.DataFrame(
        {
            "travel_id": [201, 202],
            "motive": ["9A", "1B"],                 # pro + personal
            "n_nights": [300, 300],                 # huge values -> negative mobile days before clamping
            "destination_city_category": ["C", "C"],
            "pondki": [1.0, 1.0],
            "csp": ["1", "1"],
            "n_cars": ["1", "1"],
            "city_category": ["C", "C"],
        }
    )

    trips.long_trips_db = pd.DataFrame(
        {
            "previous_motive": ["X", "Y"],
            "motive": ["M1", "M2"],
            "mode_id": ["car", "walk"],
            "distance": [10.0, 20.0],
            "n_other_passengers": [0, 1],
        },
        index=pd.Index([201, 202], name="travel_id"),
    )

    # Provide a reasonable pool of weekday/weekend days
    day_ids = list(range(1, 101))
    trips.days_trip_db = pd.DataFrame(
        {
            "day_id": day_ids,
            "weekday": [True] * 50 + [False] * 50,
            "pondki": [1.0] * 100,
            "csp": ["1"] * 100,
            "n_cars": ["1"] * 100,
            "city_category": ["C"] * 100,
        }
    )

    trips.short_trips_db = pd.DataFrame(
        {
            "previous_motive": ["A"] * 100,
            "motive": ["B"] * 100,
            "mode_id": ["car"] * 100,
            "distance": np.linspace(1.0, 20.0, 100),
            "n_other_passengers": [0] * 100,
        },
        index=pd.Index(day_ids, name="day_id"),
    )

    trips.p_car = pd.DataFrame({"p": [0.5]}, index=pd.Index(["1"], name="csp"))


def test_get_individual_trips_clamps_negative_mobile_days(monkeypatch, tmp_path,
                                                          fake_population_asset, patch_mobility_survey):
    # Avoid NumPy sentinel crashes
    _patch_numpy_core_methods(monkeypatch)

    # Keep any file IO inside the sandbox
    monkeypatch.setenv("MOBILITY_PACKAGE_DATA_FOLDER", str(tmp_path))

    import mobility.trips as mod

    trips = mod.Trips(fake_population_asset, source="EMP-2019")
    _seed_trips_dbs(trips)

    dataframe = trips.get_individual_trips(
        csp="1",
        csp_household="1",
        urban_unit_category="C",
        n_pers="2",
        n_cars="1",
        n_years=1,
    )

    # Should not crash, and should return a valid DataFrame
    assert isinstance(dataframe, pd.DataFrame)
    assert not dataframe.empty
    for col in ["trip_type", "previous_motive", "motive", "mode_id",
                "distance", "n_other_passengers"]:
        assert col in dataframe.columns
