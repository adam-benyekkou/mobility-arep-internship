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
    """Attach the minimal set of survey tables the method expects."""
    # Probability of immobility by csp (index must allow .xs("1"))
    trips.p_immobility = pd.DataFrame(
        {"immobility_weekday": [0.2], "immobility_weekend": [0.3]},
        index=pd.Index(["1"], name="csp"),
    )

    # Number of travels per csp -> .xs("1").squeeze().astype(int)
    trips.n_travels_db = pd.DataFrame(
        {"n_travels": [2]},
        index=pd.Index(["1"], name="csp"),
    )

    # Travels table sampled with weights + filters (csp/n_cars/city_category)
    trips.travels_db = pd.DataFrame(
        {
            "travel_id": [101, 102],
            "motive": ["9A", "1B"],                # one professional (starts with "9"), one personal
            "n_nights": [1, 2],
            "destination_city_category": ["C", "C"],
            "pondki": [1.0, 1.0],
            "csp": ["1", "1"],
            "n_cars": ["1", "1"],
            "city_category": ["C", "C"],
        }
    )

    # Long trips indexed by travel_id (columns expected by code)
    trips.long_trips_db = pd.DataFrame(
        {
            "previous_motive": ["X", "Y"],
            "motive": ["M1", "M2"],
            "mode_id": ["car", "walk"],
            "distance": [12.0, 3.4],
            "n_other_passengers": [0, 1],
        },
        index=pd.Index([101, 102], name="travel_id"),
    )

    # Days table sampled with weekday True/False + filters
    trips.days_trip_db = pd.DataFrame(
        {
            "day_id": list(range(1, 21)),
            "weekday": [True] * 10 + [False] * 10,
            "pondki": [1.0] * 20,
            "csp": ["1"] * 20,
            "n_cars": ["1"] * 20,
            "city_category": ["C"] * 20,
        }
    )

    # Short trips indexed by day_id (must include the "day_id"s above)
    trips.short_trips_db = pd.DataFrame(
        {
            "previous_motive": ["A"] * 20,
            "motive": ["B"] * 20,
            "mode_id": ["car"] * 20,
            "distance": np.linspace(1.0, 5.0, 20),
            "n_other_passengers": [0] * 20,
        },
        index=pd.Index(list(range(1, 21)), name="day_id"),
    )

    # Not used in current logic, but harmless to have
    trips.p_car = pd.DataFrame({"p": [0.5]}, index=pd.Index(["1"], name="csp"))


def test_get_individual_trips_happy_path(monkeypatch, tmp_path,
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

    assert isinstance(dataframe, pd.DataFrame)
    assert not dataframe.empty
    for col in ["trip_type", "previous_motive", "motive", "mode_id",
                "distance", "n_other_passengers"]:
        assert col in dataframe.columns
