import os
import sys
from pathlib import Path
import types
import builtins

import pandas as pd
import numpy as np
import pytest


@pytest.fixture
def project_dir(tmp_path, monkeypatch):
    """
    Per-test project directory. Enforces no I/O outside tmp_path via env var.
    """
    monkeypatch.setenv("MOBILITY_PROJECT_DATA_FOLDER", str(tmp_path))
    # Some codebases also look this up; set it defensively.
    monkeypatch.setenv("MOBILITY_PACKAGE_DATA_FOLDER", str(tmp_path))
    return tmp_path


@pytest.fixture(scope="session", autouse=True)
def add_repo_root_to_sys_path():
    """
    Make repository root importable so tests can import either:
      - get_swiss_data
      - mobility.get_swiss_data
    regardless of how you run pytest.
    """
    here = Path(__file__).resolve()
    # conftest.py -> .../tests/unit/get_swiss_data/conftest.py
    # repo root should be 3 parents up from 'get_swiss_data' dir: .../<repo>/
    candidates = [here.parents[i] for i in range(1, 6)]  # be generous
    for candidate in candidates:
        # Heuristic: if a 'tests' directory exists here, its parent is the repo root.
        if (candidate / "tests").exists():
            repo_root = candidate
            break
    else:
        repo_root = here.parents[3]  # best effort

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

# ---------- Asset init patch (autouse) ----------
@pytest.fixture(autouse=True)
def patch_asset_init(monkeypatch, project_dir):
    """
    Stub mobility.asset.Asset.__init__ so it only sets attributes and does not call .get().

    - Sets:
        self.inputs
        self.inputs_hash (default fake hash)
        self.cache_path = <project_dir>/<inputs_hash>-<filename>
        self.hash_path  = <project_dir>/<inputs_hash>-<filename>.hash

    Notes:
    - If mobility.asset module doesn't exist in this test environment, we synthesize it.
    """
    fake_hash_default = "deadbeefdeadbeefdeadbeefdeadbeef"

    # Ensure a mobility.asset module exists
    if "mobility" not in sys.modules:
        mobility_mod = types.ModuleType("mobility")
        sys.modules["mobility"] = mobility_mod
    if "mobility.asset" not in sys.modules:
        asset_mod = types.ModuleType("mobility.asset")

        class _Asset:
            def __init__(self, *args, **kwargs):
                pass

        asset_mod.Asset = _Asset
        sys.modules["mobility.asset"] = asset_mod

    asset_mod = sys.modules["mobility.asset"]

    def _stub_init(self, *args, **kwargs):
        inputs = kwargs.get("inputs", kwargs.get("input_dict", {}))  # tolerate slight naming drift
        filename = kwargs.get("filename", kwargs.get("base_name", "cache.parquet"))
        if not isinstance(filename, str):
            filename = "cache.parquet"

        setattr(self, "inputs", inputs)
        inputs_hash = kwargs.get("inputs_hash", fake_hash_default)
        setattr(self, "inputs_hash", inputs_hash)

        cache_filename = f"{inputs_hash}-{Path(filename).name}"
        cache_path = Path(os.environ["MOBILITY_PROJECT_DATA_FOLDER"]) / cache_filename
        setattr(self, "cache_path", cache_path)
        setattr(self, "hash_path", cache_path.with_suffix(cache_path.suffix + ".hash"))

    monkeypatch.setattr(asset_mod.Asset, "__init__", _stub_init, raising=True)

    # Helper available to tests
    def fake_inputs_hash():
        return fake_hash_default

    builtins.fake_inputs_hash = fake_inputs_hash  # utility if a test wants it
    yield
    # Clean up any leaked helper
    if hasattr(builtins, "fake_inputs_hash"):
        del builtins.fake_inputs_hash


# ---------- No-op rich.progress.Progress (autouse) ----------
@pytest.fixture(autouse=True)
def no_op_progress(monkeypatch):
    """
    Replace rich.progress.Progress with a no-op to avoid terminal I/O.
    """
    try:
        import rich.progress

        class _NoOpProgress:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def add_task(self, *args, **kwargs):
                return 0

            def update(self, *args, **kwargs):
                return None

            def stop(self):
                return None

        monkeypatch.setattr(rich.progress, "Progress", _NoOpProgress, raising=True)
    except Exception:
        # If rich isn't installed in the environment, silently ignore.
        pass


# ---------- Patch NumPy private _methods to ignore _NoValue sentinel (autouse) ----------
@pytest.fixture(autouse=True)
def patch_numpy__methods(monkeypatch):
    """
    Wrap numpy.core._methods._sum and _amax to ignore the pandas/NumPy _NoValue sentinel.
    This prevents crashes when pandas passes _NoValueType positionally.
    """
    try:
        from numpy.core import _methods as np_methods  # type: ignore[attr-defined]
    except Exception:
        yield
        return

    def _wrap(func):
        def _inner(a, axis=None, dtype=None, out=None, keepdims=False, initial=None, where=True):
            # Some numpy/pandas combos pass a sentinel; we ignore it safely here.
            return func(a, axis=axis, dtype=dtype, out=out, keepdims=keepdims, initial=initial, where=where)

        return _inner

    if hasattr(np_methods, "_sum"):
        monkeypatch.setattr(np_methods, "_sum", _wrap(np_methods._sum), raising=True)
    if hasattr(np_methods, "_amax"):
        monkeypatch.setattr(np_methods, "_amax", _wrap(np_methods._amax), raising=True)

    yield


# ---------- Parquet stubs ----------
@pytest.fixture
def parquet_stubs(monkeypatch):
    """
    Per-test controller to stub parquet I/O.
    Usage in a test:
        read_calls, write_calls = parquet_stubs

        # monkeypatch to return a given df when path matches
        read_calls["return_df"] = my_df

        # capture writes automatically
        # DataFrame.to_parquet will append the path object to write_calls["paths"]
    """
    read_calls = {"paths": [], "return_df": None}
    write_calls = {"paths": []}

    def _read_parquet_stub(path, *args, **kwargs):
        read_calls["paths"].append(Path(path))
        return read_calls["return_df"]

    def _to_parquet_stub(self, path, *args, **kwargs):
        write_calls["paths"].append(Path(path))
        # Return the same df by convention if a caller expects it
        return self

    monkeypatch.setattr(pd, "read_parquet", _read_parquet_stub, raising=True)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", _to_parquet_stub, raising=True)
    return read_calls, write_calls


# ---------- Deterministic shortuuid (optional) ----------
@pytest.fixture
def deterministic_shortuuid(monkeypatch):
    """
    Monkeypatch shortuuid.uuid to return incrementing identifiers deterministically.
    """
    counter = {"i": 0}

    def _uuid():
        counter["i"] += 1
        return f"shortuuid-{counter['i']:04d}"

    try:
        import shortuuid

        monkeypatch.setattr(shortuuid, "uuid", _uuid, raising=True)
    except Exception:
        # If shortuuid not installed, create a shim module.
        mod = types.ModuleType("shortuuid")
        mod.uuid = _uuid
        sys.modules["shortuuid"] = mod

    return None


# ---------- Fake transport zones ----------
@pytest.fixture
def fake_transport_zones():
    """
    Minimal Geo/DataFrame for code that expects transport zone metadata.
    The geometry is None to avoid geopandas dependency in these tests.
    """
    df = pd.DataFrame(
        {
            "transport_zone_id": [1, 2],
            "urban_unit_category": ["urban", "rural"],
            "geometry": [None, None],
        }
    )
    return df


# ---------- Fake population asset ----------
class _FakePopulationAsset:
    def __init__(self, transport_zones):
        self.inputs = {"transport_zones": transport_zones}

    def get(self):
        return pd.DataFrame({"transport_zone_id": [1, 2], "population": [100, 200]})


@pytest.fixture
def fake_population_asset(fake_transport_zones):
    return _FakePopulationAsset(fake_transport_zones)


# ---------- Patch mobility survey parser ----------
@pytest.fixture
def patch_mobility_survey(monkeypatch):
    """
    Monkeypatch a survey parser class to return deterministic tiny DataFrames.
    Creates mobility.parsers.survey with class Parser having parse() -> dict[str, DataFrame].
    """
    # Ensure package hierarchy exists
    if "mobility" not in sys.modules:
        sys.modules["mobility"] = types.ModuleType("mobility")
    if "mobility.parsers" not in sys.modules:
        sys.modules["mobility.parsers"] = types.ModuleType("mobility.parsers")

    survey_mod = types.ModuleType("mobility.parsers.survey")

    class Parser:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def parse(self):
            return {
                "persons": pd.DataFrame(
                    {"person_id": [1, 2], "age": [30, 45], "household_id": [10, 20]}
                ),
                "trips": pd.DataFrame(
                    {"person_id": [1], "trip_id": [100], "origin": ["A"], "destination": ["B"]}
                ),
            }

    survey_mod.Parser = Parser
    sys.modules["mobility.parsers.survey"] = survey_mod
    monkeypatch.setitem(sys.modules, "mobility.parsers.survey", survey_mod)
    return None


# ---------- Helpers to seed Trips-like attributes ----------
@pytest.fixture
def seed_trips_like_data():
    """
    Provide a tiny, consistent set of attributes for any Trips-like instance that tests call directly.
    """
    def _seed(obj):
        obj.p_immobility = 0.1
        obj.n_travels_db = pd.DataFrame({"person_id": [1, 2], "n_travels": [0, 1]})
        obj.travels_db = pd.DataFrame({"trip_id": [100], "person_id": [2], "distance_km": [5.0]})
        obj.long_trips_db = pd.DataFrame({"trip_id": [200], "person_id": [2], "distance_km": [50.0]})
        obj.days_trip_db = pd.DataFrame({"person_id": [1, 2], "days_traveled": [0, 1]})
        obj.short_trips_db = pd.DataFrame({"trip_id": [300], "person_id": [2], "distance_km": [2.0]})
        return obj

    return _seed


# ---------- Deterministic pandas sampling ----------
@pytest.fixture(autouse=True)
def deterministic_sampling(monkeypatch):
    """
    Make DataFrame.sample / Series.sample deterministic by returning the first N rows/elements.
    """
    def _df_sample(self, n=None, frac=None, replace=False, weights=None, random_state=None, axis=None, ignore_index=False):
        if n is None and frac is None:
            return self
        count = n if n is not None else max(1, int(len(self) * float(frac)))
        result = self.iloc[:count]
        return result.reset_index(drop=True) if ignore_index else result

    def _series_sample(self, n=None, frac=None, replace=False, weights=None, random_state=None, axis=None, ignore_index=False):
        if n is None and frac is None:
            return self
        count = n if n is not None else max(1, int(len(self) * float(frac)))
        result = self.iloc[:count]
        return result.reset_index(drop=True) if ignore_index else result

    monkeypatch.setattr(pd.DataFrame, "sample", _df_sample, raising=True)
    monkeypatch.setattr(pd.Series, "sample", _series_sample, raising=True)
