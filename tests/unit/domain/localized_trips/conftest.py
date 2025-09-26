# tests/unit/localized_trips/conftest.py
import os
import pathlib
import types
import pytest
import pandas as pandas
import numpy as numpy

# ----------------------------
# Core env & hashing utilities
# ----------------------------
@pytest.fixture(scope="session")
def fake_inputs_hash():
    return "deadbeefdeadbeefdeadbeefdeadbeef"

@pytest.fixture(scope="session")
def localized_trips_base_filename():
    return "trips_localized.parquet"

@pytest.fixture
def project_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("MOBILITY_PROJECT_DATA_FOLDER", str(tmp_path))
    monkeypatch.setenv("MOBILITY_PACKAGE_DATA_FOLDER", str(tmp_path))
    return tmp_path

# -------------------------------------------
# Patch Asset.__init__ to be side-effect free
# -------------------------------------------
@pytest.fixture(autouse=True)
def patch_asset_init(monkeypatch, project_dir, fake_inputs_hash):
    """
    Stub mobility.asset.Asset.__init__ so it only sets:
      - inputs
      - cache_path (if path-like => <project_dir>/<hash>-<filename>; else keep as-is, e.g. dict)
      - hash_path
      - inputs_hash
    and does NOT call .get().
    """
    import importlib
    asset_module = importlib.import_module("mobility.asset")

    def is_path_like(value):
        try:
            os.fspath(value)
            return True
        except TypeError:
            return False

    def fake_init(self, inputs, cache_path):
        self.inputs = inputs
        self.inputs_hash = fake_inputs_hash
        if is_path_like(cache_path):
            base_name = pathlib.Path(cache_path).name
            self.cache_path = pathlib.Path(project_dir) / f"{fake_inputs_hash}-{base_name}"
        else:
            self.cache_path = cache_path
        self.hash_path = pathlib.Path(project_dir) / f"{fake_inputs_hash}.hash"

    monkeypatch.setattr(asset_module.Asset, "__init__", fake_init, raising=True)
    yield

# ----------------------------
# Rich progress -> no-op stub
# ----------------------------
@pytest.fixture(autouse=True)
def no_op_progress(monkeypatch):
    class NoOpProgress:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *exc): return False
        def add_task(self, *args, **kwargs): return 0
        def update(self, *args, **kwargs): pass
        def stop(self): pass
        def start(self): pass

    try:
        import rich.progress as rich_progress
        monkeypatch.setattr(rich_progress, "Progress", NoOpProgress, raising=True)
    except Exception:
        pass
    yield

# ---------------------------------------------------------
# NumPy private reducers: replace with safe nan-aware shims
# ---------------------------------------------------------
@pytest.fixture(autouse=True)
def patch_numpy__methods(monkeypatch):
    """
    Replace NumPy private reducers to avoid forwarding numpy._NoValue into C ufuncs.
    Implementations normalize _NoValue and call nan-aware public reducers.
    """
    try:
        from numpy._core import _methods as numpy_private_methods  # type: ignore
    except Exception:
        from numpy.core import _methods as numpy_private_methods  # type: ignore

    def _normalize(axis=None, dtype=None, out=None, keepdims=False, initial=None, where=True):
        if hasattr(numpy, "_NoValue"):
            if axis is numpy._NoValue: axis = None
            if dtype is numpy._NoValue: dtype = None
            if out is numpy._NoValue: out = None
            if keepdims is numpy._NoValue: keepdims = False
            if initial is numpy._NoValue: initial = None
            if where is numpy._NoValue: where = True
        return axis, dtype, out, bool(keepdims), initial, bool(where)

    def _apply_out_keepdims(result, out, keepdims):
        if keepdims and not numpy.isscalar(result):
            result = numpy.asarray(result)
        if out is not None:
            out[...] = result
            return out
        return result

    def safe_amax(a, axis=None, dtype=None, out=None, keepdims=False, initial=None, where=True):
        axis, dtype, out, keepdims, initial, where = _normalize(axis, dtype, out, keepdims, initial, where)
        arr = numpy.asarray(a)
        # 'where' handling: if mask zeros out everything and initial given, return it
        if isinstance(where, numpy.ndarray) and where.shape != () and not where.any() and initial is not None:
            return _apply_out_keepdims(initial, out, keepdims)
        try:
            res = numpy.nanmax(arr, axis=axis, keepdims=keepdims)
        except ValueError:
            if initial is not None:
                return _apply_out_keepdims(initial, out, keepdims)
            res = numpy.max(arr, axis=axis, keepdims=keepdims)
        return _apply_out_keepdims(res, out, keepdims)

    def safe_amin(a, axis=None, dtype=None, out=None, keepdims=False, initial=None, where=True):
        axis, dtype, out, keepdims, initial, where = _normalize(axis, dtype, out, keepdims, initial, where)
        arr = numpy.asarray(a)
        if isinstance(where, numpy.ndarray) and where.shape != () and not where.any() and initial is not None:
            return _apply_out_keepdims(initial, out, keepdims)
        try:
            res = numpy.nanmin(arr, axis=axis, keepdims=keepdims)
        except ValueError:
            if initial is not None:
                return _apply_out_keepdims(initial, out, keepdims)
            res = numpy.min(arr, axis=axis, keepdims=keepdims)
        return _apply_out_keepdims(res, out, keepdims)

    def safe_sum(a, axis=None, dtype=None, out=None, keepdims=False, initial=None, where=True):
        axis, dtype, out, keepdims, initial, where = _normalize(axis, dtype, out, keepdims, initial, where)
        arr = numpy.asarray(a)
        res = numpy.nansum(arr, axis=axis, dtype=dtype, keepdims=keepdims)
        if initial not in (None, 0):
            res = res + initial
        return _apply_out_keepdims(res, out, keepdims)

    if hasattr(numpy_private_methods, "_amax"):
        monkeypatch.setattr(numpy_private_methods, "_amax", safe_amax, raising=False)
    if hasattr(numpy_private_methods, "_amin"):
        monkeypatch.setattr(numpy_private_methods, "_amin", safe_amin, raising=False)
    if hasattr(numpy_private_methods, "_sum"):
        monkeypatch.setattr(numpy_private_methods, "_sum", safe_sum, raising=False)

    yield

# ------------------------------------------------------------
# Deterministic pandas sampling (avoid randomness in unit tests)
# ------------------------------------------------------------
@pytest.fixture(autouse=True)
def deterministic_pandas_sample(monkeypatch):
    def dataframe_sample(self, n=None, frac=None, replace=False, weights=None, random_state=None, axis=None, **kwargs):
        if frac is not None:
            n = int(len(self) * float(frac))
        if n is None:
            n = 1
        return self.head(n)

    def series_sample(self, n=None, frac=None, replace=False, weights=None, random_state=None, **kwargs):
        if frac is not None:
            n = int(len(self) * float(frac))
        if n is None:
            n = 1
        return self.head(n)

    monkeypatch.setattr(pandas.DataFrame, "sample", dataframe_sample, raising=False)
    monkeypatch.setattr(pandas.Series, "sample", series_sample, raising=False)
    yield

# -----------------------
# Parquet read/write stubs
# -----------------------
@pytest.fixture
def parquet_stubs(monkeypatch):
    parquet_capture = types.SimpleNamespace()
    parquet_capture.read_calls = []
    parquet_capture.write_calls = []

    def stub_read(return_dataframe):
        def read_parquet_stub(path, *args, **kwargs):
            parquet_capture.read_calls.append(pathlib.Path(path))
            return return_dataframe
        monkeypatch.setattr(pandas, "read_parquet", read_parquet_stub, raising=True)
        return parquet_capture

    def stub_write():
        def to_parquet_stub(self, path, *args, **kwargs):
            parquet_capture.write_calls.append(pathlib.Path(path))
            return None
        monkeypatch.setattr(pandas.DataFrame, "to_parquet", to_parquet_stub, raising=True)
        return parquet_capture

    parquet_capture.stub_read = stub_read
    parquet_capture.stub_write = stub_write
    return parquet_capture

# -----------------------------------
# Minimal transport zones & population
# -----------------------------------
@pytest.fixture
def fake_transport_zones():
    return pandas.DataFrame({
        "transport_zone_id": [1, 2, 3],
        "urban_unit_category": ["A", "B", "C"],
        "geometry": [None, None, None],
    })

@pytest.fixture
def fake_population_asset(fake_transport_zones):
    class FakePopulationAsset:
        def __init__(self):
            self.inputs = {"transport_zones": fake_transport_zones}
        def get(self):
            return pandas.DataFrame({
                "individual_id": [10, 20, 30],
                "transport_zone_id": [1, 2, 3],
            })
    return FakePopulationAsset()

# ---------------------------------------------------
# Helpers to build Trips-like objects for the tests
# ---------------------------------------------------
@pytest.fixture
def make_fake_trips_asset(fake_population_asset):
    def factory(trips_dataframe=None, population_asset=fake_population_asset):
        class FakeTripsAsset:
            def __init__(self, trips_dataframe, population_asset):
                self.inputs = {"population": population_asset}
                self._dataframe = trips_dataframe if trips_dataframe is not None else pandas.DataFrame({
                    "trip_id": [1, 2],
                    "individual_id": [10, 20],
                    "previous_motive": ["1.1", "9.91"],
                    "motive": ["9.91", "1.1"],
                    "mode_id": [0, 0],
                    "distance": [0.0, 0.0],
                })
            def get(self):
                return self._dataframe.copy()
        return FakeTripsAsset(trips_dataframe, population_asset)
    return factory

# -----------------------------
# Sanitize NumPy _NoValue leaks
# -----------------------------
@pytest.fixture(autouse=True)
def sanitize_novalue_in_melt(monkeypatch):
    """
    LocalizedTrips.sample_modes -> .melt(...) then .astype(int) on the 'value' column.
    If _NoValue leaks into 'value', int(_NoValue) raises TypeError.
    We sanitize melt's return.
    """
    original_dataframe_melt = pandas.DataFrame.melt

    def dataframe_melt_safe(self, *args, **kwargs):
        result = original_dataframe_melt(self, *args, **kwargs)
        if hasattr(numpy, "_NoValue"):
            try:
                return result.replace({numpy._NoValue: numpy.nan})
            except Exception:
                pass
        return result

    monkeypatch.setattr(pandas.DataFrame, "melt", dataframe_melt_safe, raising=False)

@pytest.fixture(autouse=True)
def sanitize_novalue_before_astype(monkeypatch):
    """
    Secondary guard: if _NoValue still reaches a Series/DataFrame just before
    .astype(...), replace with NaN.
    """
    original_series_astype = pandas.Series.astype
    original_dataframe_astype = pandas.DataFrame.astype

    def replace_novalue(obj):
        if hasattr(numpy, "_NoValue"):
            try:
                return obj.replace({numpy._NoValue: numpy.nan})
            except Exception:
                try:
                    return obj.where(~obj.apply(lambda v: v is numpy._NoValue), other=numpy.nan)
                except Exception:
                    return obj
        return obj

    def series_astype_safe(self, dtype=None, *args, **kwargs):
        return original_series_astype(replace_novalue(self), dtype=dtype, *args, **kwargs)

    def dataframe_astype_safe(self, dtype=None, *args, **kwargs):
        return original_dataframe_astype(replace_novalue(self), dtype=dtype, *args, **kwargs)

    monkeypatch.setattr(pandas.Series, "astype", series_astype_safe, raising=False)
    monkeypatch.setattr(pandas.DataFrame, "astype", dataframe_astype_safe, raising=False)

# ----------------------------------------------------------
# Choice/cost model stubs — patch both source modules and module-level names
# ----------------------------------------------------------
@pytest.fixture
def patch_choice_models(monkeypatch, fake_transport_zones):
    import importlib

    registry = types.SimpleNamespace()
    registry.travel_costs_constructor_args = None
    registry.transport_mode_constructor_args = None
    registry.work_destination_constructor_args = None

    class TravelCostsStub:
        def __init__(self, transport_zones_dataframe):
            registry.travel_costs_constructor_args = {"transport_zones": transport_zones_dataframe}
        def get(self):
            return pandas.DataFrame({
                "from": [1, 2],
                "to": [2, 1],
                "mode": [1, 1],
                "distance": [10.0, 12.0],
            }).set_index(["from", "to", "mode"])

    class TransportModeChoiceStub:
        def __init__(self, travel_costs_asset, cost_of_time):
            registry.transport_mode_constructor_args = {"travel_costs": travel_costs_asset, "cost_of_time": cost_of_time}
        def get(self):
            return pandas.DataFrame({
                "from": [1, 2],
                "to": [2, 1],
                "mode": [1, 1],
                "prob": [0.9, 0.8],
            }).set_index(["from", "to", "mode"])

    class WorkDestinationChoiceStub:
        def __init__(self, transport_zones_dataframe, travel_costs_asset, cost_of_time, alpha, beta):
            registry.work_destination_constructor_args = {
                "transport_zones": transport_zones_dataframe,
                "travel_costs": travel_costs_asset,
                "cost_of_time": cost_of_time,
                "alpha": alpha,
                "beta": beta,
            }
        def get(self):
            return pandas.DataFrame({
                "transport_zone_id": [1, 2, 3],
                "to_transport_zone_id": [2, 1, 3],
                "p": [0.6, 0.7, 1.0],
            })

    # Patch the source modules
    multimodal_module = importlib.import_module("mobility.multimodal_travel_costs")
    transport_mode_module = importlib.import_module("mobility.transport_mode_choice_model")
    work_destination_module = importlib.import_module("mobility.work_destination_choice_model")
    monkeypatch.setattr(multimodal_module, "MultimodalTravelCosts", TravelCostsStub, raising=True)
    monkeypatch.setattr(transport_mode_module, "TransportModeChoiceModel", TransportModeChoiceStub, raising=True)
    monkeypatch.setattr(work_destination_module, "WorkDestinationChoiceModel", WorkDestinationChoiceStub, raising=True)

    # Also patch the already-imported names inside mobility.localized_trips
    localized_trips_module = importlib.import_module("mobility.localized_trips")
    monkeypatch.setattr(localized_trips_module, "MultimodalTravelCosts", TravelCostsStub, raising=True)
    monkeypatch.setattr(localized_trips_module, "TransportModeChoiceModel", TransportModeChoiceStub, raising=True)
    monkeypatch.setattr(localized_trips_module, "WorkDestinationChoiceModel", WorkDestinationChoiceStub, raising=True)

    return registry
