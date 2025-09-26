from __future__ import annotations

import os
import sys
import types
from pathlib import Path
import pytest
import pandas as pd

# ---------------------------------------------------------
# Bootstrap modules needed at import time (session, autouse)
# ---------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def bootstrap_rich_progress_module():
    """Ensure rich.progress.Progress exists before any code imports it."""
    if "rich" not in sys.modules:
        sys.modules["rich"] = types.ModuleType("rich")
    if "rich.progress" not in sys.modules:
        sys.modules["rich.progress"] = types.ModuleType("rich.progress")

    class SessionNoOpProgress:
        def __init__(self, *_, **__): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False
        def add_task(self, *_, **__): return 0
        def update(self, *_, **__): return None
        def advance(self, *_, **__): return None

    setattr(sys.modules["rich.progress"], "Progress", SessionNoOpProgress)


@pytest.fixture(scope="session", autouse=True)
def inject_minimal_modules():
    """Provide minimal stubs so mobility.work_destination_choice_model imports cleanly."""
    # Fake geopandas: only need GeoDataFrame symbol
    if "geopandas" not in sys.modules:
        geopandas_module = types.ModuleType("geopandas")
        setattr(geopandas_module, "GeoDataFrame", pd.DataFrame)  # alias for tests
        sys.modules["geopandas"] = geopandas_module

    # mobility package skeleton
    if "mobility" not in sys.modules:
        mobility_package = types.ModuleType("mobility")
        mobility_package.__path__ = []
        sys.modules["mobility"] = mobility_package

    # mobility.asset
    if "mobility.asset" not in sys.modules:
        asset_module = types.ModuleType("mobility.asset")

        class DummyAsset:
            def __init__(self, *args, **kwargs):
                pass  # will be monkeypatched by patch_asset_init

        setattr(asset_module, "Asset", DummyAsset)
        sys.modules["mobility.asset"] = asset_module

    # mobility.destination_choice_model (base stub)
    if "mobility.destination_choice_model" not in sys.modules:
        destination_choice_model_module = types.ModuleType("mobility.destination_choice_model")

        class DummyDestinationChoiceModel:
            def __init__(self, *args, **kwargs):
                self._init_args = args
                self._init_kwargs = kwargs

        setattr(destination_choice_model_module, "DestinationChoiceModel", DummyDestinationChoiceModel)
        sys.modules["mobility.destination_choice_model"] = destination_choice_model_module

    # mobility.parsers.jobs_active_population_distribution
    if "mobility.parsers" not in sys.modules:
        parsers_package = types.ModuleType("mobility.parsers")
        parsers_package.__path__ = []
        sys.modules["mobility.parsers"] = parsers_package

    if "mobility.parsers.jobs_active_population_distribution" not in sys.modules:
        jobs_active_population_distribution_module = types.ModuleType(
            "mobility.parsers.jobs_active_population_distribution"
        )

        class DummyJobsActivePopulationDistribution:
            def get(self):
                index = pd.Index(["X1", "X2"], name="CODGEO")
                active_population = pd.DataFrame({"colA": [1, 2]}, index=index)
                jobs = pd.DataFrame({"colB": [3, 4]}, index=index)
                return active_population, jobs

        setattr(
            jobs_active_population_distribution_module,
            "JobsActivePopulationDistribution",
            DummyJobsActivePopulationDistribution,
        )
        sys.modules["mobility.parsers.jobs_active_population_distribution"] = (
            jobs_active_population_distribution_module
        )

    # shortuuid (optional dependency)
    if "shortuuid" not in sys.modules:
        shortuuid_module = types.ModuleType("shortuuid")

        def stub_uuid():
            return "stub-uuid"

        setattr(shortuuid_module, "uuid", stub_uuid)
        sys.modules["shortuuid"] = shortuuid_module


# ---------------------------------------------------------
# Robust, early patch of numpy _NoValue so pandas sees the safe version
# ---------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def patch_numpy_novalue_session():
    """
    Replace NumPy's private sentinel _NoValue with a zero-like object in all
    common import locations (numpy, numpy.core, numpy.core._multiarray_umath),
    before pandas/NumPy cache it.
    """
    try:
        import numpy as np
    except Exception:
        return  # NumPy not available; nothing to do

    class ZeroLikeNoValue:
        def __int__(self): return 0
        def __float__(self): return 0.0
        def __index__(self): return 0
        def __bool__(self): return False
        def __repr__(self): return "_NoValue(0)"

    zero_like_no_value = ZeroLikeNoValue()

    try:
        np._NoValue = zero_like_no_value  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        import numpy.core as numpy_core
        numpy_core._NoValue = zero_like_no_value  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        from numpy.core import _multiarray_umath as numpy_core_multiarray_umath  # type: ignore
        numpy_core_multiarray_umath._NoValue = zero_like_no_value  # type: ignore[attr-defined]
    except Exception:
        pass


# ---------------------------------------------------------
# Environment / paths
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def autouse_project_env(tmp_path, monkeypatch):
    """Always set MOBILITY_PROJECT_DATA_FOLDER for each test function."""
    monkeypatch.setenv("MOBILITY_PROJECT_DATA_FOLDER", str(tmp_path))


@pytest.fixture()
def project_dir(tmp_path):
    """If a test wants the actual Path, it can request project_dir."""
    return Path(tmp_path)


# ---------------------------------------------------------
# Asset init patching / hash helper
# ---------------------------------------------------------

@pytest.fixture(scope="session")
def fake_inputs_hash():
    return "deadbeefdeadbeefdeadbeefdeadbeef"


@pytest.fixture(autouse=True)
def patch_asset_init(monkeypatch, project_dir, fake_inputs_hash):
    """
    Stub mobility.asset.Asset.__init__ to only set attributes and NOT call .get().
    cache_path = <project_dir>/<fake_inputs_hash>-<filename>
    """
    import mobility.asset as asset_module

    def asset_init_stub(self, *args, **kwargs):
        filename = kwargs.get("filename") or getattr(self, "base_name", "asset") + ".parquet"
        self.inputs = kwargs.get("inputs", {})
        self.inputs_hash = fake_inputs_hash
        file_name = f"{fake_inputs_hash}-{Path(filename).name}"
        self.cache_path = Path(project_dir) / file_name
        self.hash_path = Path(project_dir) / f"{fake_inputs_hash}.sha1"
        # DO NOT call self.get()

    monkeypatch.setattr(asset_module.Asset, "__init__", asset_init_stub, raising=True)


# ---------------------------------------------------------
# No-op progress (per-test monkeypatch; session bootstrap already set)
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def no_op_progress(monkeypatch):
    rich_progress_module = sys.modules["rich.progress"]

    class NoOpProgress:
        def __init__(self, *_, **__): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False
        def add_task(self, *_, **__): return 0
        def update(self, *_, **__): return None
        def advance(self, *_, **__): return None

    monkeypatch.setattr(rich_progress_module, "Progress", NoOpProgress, raising=True)


# ---------------------------------------------------------
# NumPy private _methods patch (replace _sum and _amax with safe shims)
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def patch_numpy__methods(monkeypatch):
    """
    Replace NumPy private reducers (_methods._sum and _methods._amax in both
    numpy._methods and numpy.core._methods) with safe shims that normalize
    the 'initial' argument when NumPy's private sentinel is present.
    """
    try:
        import numpy as np
    except Exception:
        return

    # Try to import both possible modules where _methods can live
    numpy_methods_module = None
    numpy_core_methods_module = None
    try:
        from numpy import _methods as numpy_methods_module  # type: ignore
    except Exception:
        pass
    try:
        from numpy.core import _methods as numpy_core_methods_module  # type: ignore
    except Exception:
        pass

    def normalize_initial(initial_value, default_value):
        type_name = getattr(type(initial_value), "__name__", "")
        if initial_value is None or type_name == "_NoValueType":
            return default_value
        return initial_value

    def safe_sum(array, axis=None, dtype=None, out=None, keepdims=False, initial=None, where=True):
        try:
            initial = normalize_initial(initial, 0)
            return np.add.reduce(
                array, axis=axis, dtype=dtype, out=out, keepdims=keepdims, initial=initial, where=where
            )
        except TypeError:
            try:
                initial = normalize_initial(initial, 0)
                return np.add.reduce(array, axis=axis, dtype=dtype, out=out, keepdims=keepdims, initial=initial)
            except TypeError:
                return np.add.reduce(array, axis=axis, dtype=dtype, out=out, keepdims=keepdims)

    def default_for_amax_dtype(dtype):
        """Return a neutral 'very small' value appropriate for dtype."""
        kind = dtype.kind
        if kind in ("i", "u"):  # signed/unsigned integers
            return int(np.iinfo(dtype).min)
        if kind == "b":         # boolean
            return False
        if kind == "f":         # floats
            return -np.inf
        # Fallback for anything unexpected: do not set an initial
        return None

    def safe_amax(array, axis=None, out=None, keepdims=False, initial=None, where=True):
        try:
            array_np = np.asarray(array)
            inferred_default = default_for_amax_dtype(array_np.dtype)
            initial = normalize_initial(initial, inferred_default)
            if initial is None:
                # Avoid passing an initial the dtype cannot accept
                return np.maximum.reduce(array_np, axis=axis, out=out, keepdims=keepdims, where=where)
            return np.maximum.reduce(
                array_np, axis=axis, out=out, keepdims=keepdims, initial=initial, where=where
            )
        except TypeError:
            try:
                array_np = np.asarray(array)
                inferred_default = default_for_amax_dtype(array_np.dtype)
                initial = normalize_initial(initial, inferred_default)
                if initial is None:
                    return np.maximum.reduce(array_np, axis=axis, out=out, keepdims=keepdims)
                return np.maximum.reduce(array_np, axis=axis, out=out, keepdims=keepdims, initial=initial)
            except TypeError:
                return np.maximum.reduce(np.asarray(array), axis=axis, out=out, keepdims=keepdims)

    for module in (numpy_methods_module, numpy_core_methods_module):
        if module is not None:
            if hasattr(module, "_sum"):
                monkeypatch.setattr(module, "_sum", safe_sum, raising=True)
            if hasattr(module, "_amax"):
                monkeypatch.setattr(module, "_amax", safe_amax, raising=True)


# ---------------------------------------------------------
# Pure-Python pandas sum overrides (bullet-proof against _NoValue)
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def patch_pandas_sum(monkeypatch):
    """
    Fully override pandas Series.sum / DataFrame.sum with small pure-Python
    versions that ignore NumPy internals and `_NoValue` sentinels.
    """
    import builtins
    import pandas as pd

    def python_sum_iter(values, skipna=True):
        if skipna:
            values = (v for v in values if pd.notna(v))
        return builtins.sum(values)

    def series_sum(self, axis=None, skipna=True, *args, **kwargs):
        return python_sum_iter(self.array, skipna=skipna)

    def dataframe_sum(self, axis=0, skipna=True, *args, **kwargs):
        if axis in (1, "columns"):
            return self.apply(lambda row: python_sum_iter(row.values, skipna=skipna), axis=1)
        else:
            return self.apply(lambda col: python_sum_iter(col.values, skipna=skipna), axis=0)

    monkeypatch.setattr(pd.Series, "sum", series_sum, raising=True)
    monkeypatch.setattr(pd.DataFrame, "sum", dataframe_sum, raising=True)


# ---------------------------------------------------------
# Parquet stubs
# ---------------------------------------------------------

class ParquetStubs:
    def __init__(self, monkeypatch):
        self._read_result = None
        self.written_paths = []
        self.last_read_path = None

        def read_parquet_stub(path, *args, **kwargs):
            self.last_read_path = Path(path)
            return self._read_result if self._read_result is not None else pd.DataFrame({"x": [1, 2]})

        def to_parquet_stub(dataframe, path, *args, **kwargs):
            self.written_paths.append(Path(path))

        import pandas as pandas_module
        monkeypatch.setattr(pandas_module, "read_parquet", read_parquet_stub, raising=True)
        monkeypatch.setattr(pandas_module.DataFrame, "to_parquet", to_parquet_stub, raising=True)

    def set_read_result(self, dataframe: pd.DataFrame):
        self._read_result = dataframe


@pytest.fixture
def parquet_stubs(monkeypatch):
    return ParquetStubs(monkeypatch)


# ---------------------------------------------------------
# Deterministic shortuuid (optional)
# ---------------------------------------------------------

@pytest.fixture
def deterministic_shortuuid(monkeypatch):
    import shortuuid
    counter = {"i": 0}

    def deterministic_uuid():
        counter["i"] += 1
        return f"uuid-{counter['i']:04d}"

    monkeypatch.setattr(shortuuid, "uuid", deterministic_uuid, raising=True)
    return shortuuid


# ---------------------------------------------------------
# Fake data fixtures
# ---------------------------------------------------------

@pytest.fixture
def fake_transport_zones():
    """Minimal DataFrame with the columns your code expects."""
    return pd.DataFrame(
        {
            "admin_id": ["A1", "A2", "A3"],
            "transport_zone_id": [101, 102, 103],
            "geometry": [None, None, None],
        }
    )


@pytest.fixture
def fake_population_asset(fake_transport_zones):
    """Simple stand-in asset with .get() and recorded inputs."""
    class DummyPopulationAsset:
        def __init__(self, transport_zones): self.inputs = {"transport_zones": transport_zones}
        def get(self):
            return pd.DataFrame({"population": [10, 20, 30], "transport_zone_id": [101, 102, 103]})
    return DummyPopulationAsset(fake_transport_zones)


@pytest.fixture
def patch_mobility_survey():
    yield  # placeholder hook if needed later


# ---------------------------------------------------------
# Safety: no network + default env
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def enforce_no_network_and_env(monkeypatch):
    try:
        import requests
        def no_network(*args, **kwargs):
            raise RuntimeError("Network disabled in tests")
        monkeypatch.setattr(requests, "get", no_network, raising=False)
    except Exception:
        pass
    monkeypatch.setenv("MOBILITY_PACKAGE_DATA_FOLDER", os.environ.get("MOBILITY_PACKAGE_DATA_FOLDER", ""))
