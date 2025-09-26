# tests/unit/trips/conftest.py
import os
import pathlib
import pytest
import pandas as pd

DETERMINISTIC_HASH = "deadbeefdeadbeefdeadbeefdeadbeef"  # 32 hex chars

# --------------------------
# Core environment fixtures
# --------------------------

@pytest.fixture(autouse=True)
def project_dir(tmp_path, monkeypatch):
    """Always set MOBILITY_PROJECT_DATA_FOLDER for these tests."""
    monkeypatch.setenv("MOBILITY_PROJECT_DATA_FOLDER", str(tmp_path))
    return tmp_path


@pytest.fixture(autouse=True)
def patch_asset_init(monkeypatch):
    """
    Make Asset.__init__ harmless + deterministic:
    - set self.inputs
    - set self.inputs_hash to a fixed value
    - rewrite cache_path as <dir>/<DETERMINISTIC_HASH>-<basename>
    - set self.hash_path accordingly
    - DO NOT call self.get()
    """
    import mobility.asset as asset_mod

    def fake_init(self, inputs, cache_path):
        self.inputs = inputs
        self.inputs_hash = DETERMINISTIC_HASH

        if isinstance(cache_path, dict):
            fixed = {}
            for k, cp in cache_path.items():
                cp = pathlib.Path(cp)
                fixed[k] = cp.parent / f"{DETERMINISTIC_HASH}-{cp.name}"
            self.cache_path = fixed
            any_cp = next(iter(fixed.values()))
            self.hash_path = any_cp.with_suffix(".inputs-hash")
        else:
            cp = pathlib.Path(cache_path)
            self.cache_path = cp.parent / f"{DETERMINISTIC_HASH}-{cp.name}"
            self.hash_path = self.cache_path.with_suffix(".inputs-hash")

    monkeypatch.setattr(asset_mod.Asset, "__init__", fake_init, raising=True)


@pytest.fixture(autouse=True)
def no_op_progress(monkeypatch):
    """Replace rich.Progress with a no-op."""
    import mobility.trips as mod

    class ProgressNoOp:
        def __enter__(self): return self
        def __exit__(self, *exc): pass
        def add_task(self, *a, **k): return 1
        def update(self, *a, **k): pass

    monkeypatch.setattr(mod, "Progress", ProgressNoOp, raising=True)


@pytest.fixture(autouse=True)
def parquet_stubs(monkeypatch):
    """
    Stub pd.read_parquet / to_parquet.
    """
    wrote = {}

    def fake_to_parquet(self, path, *a, **k):
        wrote["path"] = str(path)
        wrote["data"] = self.copy()

    def fake_read_parquet(path, *a, **k):
        # Minimal valid default return; tests can re-patch if needed.
        return pd.DataFrame(
            {"from": [1], "to": [2], "mode": ["car"], "time": [1.0], "distance": [1.0]}
        )

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet, raising=True)
    monkeypatch.setattr(pd, "read_parquet", fake_read_parquet, raising=True)
    return wrote


@pytest.fixture(autouse=True)
def deterministic_shortuuid(monkeypatch):
    """Make shortuuid.uuid deterministic."""
    import mobility.trips as mod
    counter = {"i": 0}

    def fake_uuid():
        counter["i"] += 1
        return f"uuid-{counter['i']}"

    monkeypatch.setattr(mod.shortuuid, "uuid", fake_uuid, raising=True)


@pytest.fixture(autouse=True)
def patch_safe_sample(monkeypatch):
    """
    Deterministic safe_sample:
    - returns first n rows (repeat if needed)
    - returns empty frame when n <= 0
    """
    import mobility.trips as mod

    def fake_safe_sample(df, n, *a, **k):
        n = int(n)
        if n <= 0:
            return df.iloc[0:0].copy()
        if len(df) == 0:
            return df.copy()
        reps = (n + len(df) - 1) // len(df)
        return pd.concat([df] * reps, ignore_index=True).iloc[:n].copy()

    monkeypatch.setattr(mod, "safe_sample", fake_safe_sample, raising=True)

# --------------------------
# Domain-specific fixtures
# --------------------------

@pytest.fixture
def fake_transport_zones():
    """Minimal transport zones table used by Trips.get_population_trips merge."""
    return pd.DataFrame(
        {
            "transport_zone_id": [101, 102],
            "urban_unit_category": ["C", "B"],
        }
    )


class _FakeTZAsset:
    def __init__(self, df): self._df = df
    def get(self): return self._df


class _FakePopulationAsset:
    """Tiny stand-in for a Population Asset for Trips."""
    def __init__(self, tz_df, pop_df):
        self.inputs = {"transport_zones": _FakeTZAsset(tz_df)}
        self._df = pop_df
    def get(self): return self._df


@pytest.fixture
def fake_population_asset(fake_transport_zones):
    """Provide a fake population asset with the columns Trips expects."""
    pop = pd.DataFrame(
        {
            "individual_id": ["p1", "p2"],
            "socio_pro_category": ["A", "A"],
            "ref_pers_socio_pro_category": ["B", "B"],
            "n_pers_household": [2, 3],
            "n_cars": ["1", "0"],
            "transport_zone_id": [101, 102],
        }
    )
    return _FakePopulationAsset(fake_transport_zones, pop)


# Alias expected by tests
@pytest.fixture
def fake_population(fake_population_asset):
    return fake_population_asset


@pytest.fixture
def patch_mobility_survey(monkeypatch):
    """
    Replace MobilitySurvey with a fake that returns a complete dict
    of the frames Trips expects in create_and_get_asset.
    """
    import mobility.trips as mod
    # p_immobility indexed by CSP
    p_immobility = pd.DataFrame(
        {"immobility_weekday": [0.0], "immobility_weekend": [0.0]},
        index=pd.Index(["A"], name="csp"),
    )
    # n_travels per CSP (keep a column so .squeeze().astype(int) is valid)
    n_travels = pd.DataFrame({"n_travels": [2]}, index=pd.Index(["A"], name="csp"))
    # days db
    days_trip = pd.DataFrame(
        {
            "day_id": ["d1", "d2", "d3", "d4", "d5"],
            "weekday": [True, True, False, False, True],
            "city_category": ["C", "B", "C", "B", "C"],
            "csp": ["A", "A", "A", "A", "A"],
            "n_cars": ["1", "0", "1", "0", "1"],
            "pondki": [1.0, 1.0, 1.0, 1.0, 1.0],
        }
    )
    # short trips indexed by day_id
    short_trips = pd.DataFrame(
        {
            "previous_motive": ["x", "y", "z", "w", "t"],
            "motive": ["m1", "m2", "m3", "m4", "m5"],
            "mode_id": [1, 2, 3, 2, 1],
            "distance": [1.0, 2.0, 1.5, 3.0, 2.5],
            "n_other_passengers": [0, 1, 0, 2, 1],
        },
        index=pd.Index(days_trip["day_id"], name="day_id"),
    )
    # travels
    travels = pd.DataFrame(
        {
            "travel_id": [100, 200, 300],
            "motive": ["9-prof", "1-pers", "1-pers"],
            "n_nights": [0, 1, 2],
            "destination_city_category": ["C", "B", "C"],
            "pondki": [1.0, 1.0, 1.0],
            "csp": ["A", "A", "A"],
            "n_cars": ["1", "0", "1"],
            "city_category": ["C", "B", "C"],
        }
    )
    # long trips indexed by travel_id
    long_trips = pd.DataFrame(
        {
            "previous_motive": ["lp1", "lp2", "lp3"],
            "motive": ["L1", "L2", "L3"],
            "mode_id": [5, 6, 7],
            "distance": [10.0, 20.0, 15.0],
            "n_other_passengers": [0, 1, 2],
        },
        index=pd.Index(travels["travel_id"], name="travel_id"),
    )
    p_car = pd.DataFrame({"p": [1.0]}, index=pd.Index(["A"], name="csp"))

    payload = {
        "short_trips": short_trips,
        "days_trip": days_trip,
        "long_trips": long_trips,
        "travels": travels,
        "n_travels": n_travels,
        "p_immobility": p_immobility,
        "p_car": p_car,
    }

    class FakeMobilitySurvey:
        def __init__(self, source): self.source = source
        def get(self): return payload

    monkeypatch.setattr(mod, "MobilitySurvey", FakeMobilitySurvey, raising=True)
    return payload
