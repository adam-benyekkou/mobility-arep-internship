import os
import io
import json
import types
import pathlib
import builtins
import contextlib

import pytest
import pandas as pd
import numpy as np

# ===============================
# Core environment + path helpers
# ===============================

@pytest.fixture(scope="session")
def fake_inputs_hash():
    # 32 hex chars; used to prefix cache file names
    return "deadbeefdeadbeefdeadbeefdeadbeef"


@pytest.fixture(scope="session")
def project_dir(tmp_path_factory):
    # Per your spec: use a pytest tmp_path and set env var
    path = tmp_path_factory.mktemp("mobility_project_data")
    os.environ["MOBILITY_PROJECT_DATA_FOLDER"] = str(path)
    # The module under test also uses this one; point it to tmp as well
    package_data = tmp_path_factory.mktemp("mobility_package_data")
    os.environ["MOBILITY_PACKAGE_DATA_FOLDER"] = str(package_data)
    # Ensure the gtfs subfolder exists for metadata and downloads
    (pathlib.Path(os.environ["MOBILITY_PACKAGE_DATA_FOLDER"]) / "gtfs").mkdir(parents=True, exist_ok=True)
    return pathlib.Path(os.environ["MOBILITY_PROJECT_DATA_FOLDER"])


# =====================================
# Patch Asset.__init__ to avoid .get()
# =====================================

@pytest.fixture(autouse=True)
def patch_asset_init(monkeypatch, project_dir, fake_inputs_hash):
    """
    Stub mobility.asset.Asset.__init__ so it does NOT call .get().
    It should only set:
      - self.inputs
      - self.cache_path  -> <project_dir>/<fake_inputs_hash>-<filename>
      - self.hash_path   -> <project_dir>/<fake_inputs_hash>.sha1
      - self.inputs_hash -> fake_inputs_hash
    """
    try:
        import mobility.asset  # import here so tests that do not import mobility.* still succeed
    except Exception:
        # If the package path doesn't exist yet for some reason, create a dummy module shape
        mobility = types.SimpleNamespace()
        mobility.asset = types.SimpleNamespace()
        def _noop(*args, **kwargs): ...
        mobility.asset.Asset = type("Asset", (), {"__init__": _noop})
        builtins.__dict__.setdefault("mobility", mobility)

    def fake_asset_init(self, inputs, cache_path):
        # cache_path is a pathlib.Path; only use the name to construct the hashed file
        base_name = pathlib.Path(cache_path).name
        hashed_name = f"{fake_inputs_hash}-{base_name}"
        self.inputs = inputs
        self.inputs_hash = fake_inputs_hash
        self.cache_path = project_dir / hashed_name
        self.hash_path = project_dir / f"{fake_inputs_hash}.sha1"

    monkeypatch.setattr("mobility.asset.Asset.__init__", fake_asset_init, raising=True)


# ====================================
# No-op rich.progress.Progress fixture
# ====================================

@pytest.fixture(autouse=True)
def no_op_progress(monkeypatch):
    """Stub rich.progress.Progress to a no-op context manager and object."""
    try:
        import rich.progress as rp
    except Exception:
        return  # If rich is not importable in the environment, nothing to do

    class _NoOpProgress:
        def __init__(self, *args, **kwargs): ...
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False
        def add_task(self, *_, **__): return 0
        def update(self, *_, **__): ...
        def advance(self, *_, **__): ...
        def track(self, iterable, *args, **kwargs): 
            for item in iterable:
                yield item

    monkeypatch.setattr(rp, "Progress", _NoOpProgress, raising=True)


# ========================================================
# Wrap NumPy private _methods to ignore _NoValue sentinel
# (prevents pandas/NumPy _NoValueType crash in some flows)
# ========================================================

@pytest.fixture(autouse=True)
def patch_numpy__methods(monkeypatch):
    # Only patch if the objects exist
    if hasattr(np, "_NoValue"):
        _NoValue = np._NoValue
    else:
        class _NoValueType: 
            pass
        _NoValue = _NoValueType()

    if hasattr(np, "_methods"):
        _methods = np._methods
        if hasattr(_methods, "_sum"):
            original_sum = _methods._sum

            def wrapped_sum(a, axis=_NoValue, dtype=_NoValue, out=_NoValue, keepdims=False, initial=_NoValue, where=True):
                # Replace sentinel parameters with None or defaults acceptable by original function
                axis = None if axis is _NoValue else axis
                dtype = None if dtype is _NoValue else dtype
                out = None if out is _NoValue else out
                initial = None if initial is _NoValue else initial
                return original_sum(a, axis=axis, dtype=dtype, out=out, keepdims=keepdims, initial=initial, where=where)

            monkeypatch.setattr(_methods, "_sum", wrapped_sum, raising=True)

        if hasattr(_methods, "_amax"):
            original_amax = _methods._amax

            def wrapped_amax(a, axis=_NoValue, out=_NoValue, keepdims=False, initial=_NoValue, where=True):
                axis = None if axis is _NoValue else axis
                out = None if out is _NoValue else out
                initial = None if initial is _NoValue else initial
                return original_amax(a, axis=axis, out=out, keepdims=keepdims, initial=initial, where=where)

            monkeypatch.setattr(_methods, "_amax", wrapped_amax, raising=True)


# ==========================================
# Parquet stubs (opt-in use inside each test)
# ==========================================

@pytest.fixture
def parquet_stubs(monkeypatch):
    """
    Provide helpers to monkeypatch parquet IO for tests that need it.
    Usage within a test:
      rp = parquet_stubs["set_read"](lambda path: df)
      tp = parquet_stubs["set_write"](capture_list)
    """
    captured_write_paths = []
    read_impl = {"fn": None}

    def set_read(fn):
        read_impl["fn"] = fn
        monkeypatch.setattr(pd, "read_parquet", lambda path, *a, **k: fn(path), raising=True)

    def set_write(capture_list=None):
        def to_parquet(self, path, *args, **kwargs):
            if capture_list is not None:
                capture_list.append(path)
            return self  # behave like a no-op writer for tests
        monkeypatch.setattr(pd.DataFrame, "to_parquet", to_parquet, raising=True)

    return {"set_read": set_read, "set_write": set_write}


# ==================================
# Deterministic shortuuid (optional)
# ==================================

@pytest.fixture
def deterministic_shortuuid(monkeypatch):
    try:
        import shortuuid  # optional; only patch if present
    except Exception:
        return

    counter = {"i": 0}
    def fake_uuid():
        counter["i"] += 1
        return f"shortuuid-{counter['i']:04d}"

    monkeypatch.setattr(shortuuid, "uuid", fake_uuid, raising=True)


# ==================================================
# Minimal transport zones + population asset fakes
# ==================================================

@pytest.fixture
def fake_transport_zones(tmp_path):
    """
    Returns a tiny stand-in object with:
      - .get() -> DataFrame with expected columns
      - .cache_path -> Path needed by prepare_gtfs_router
    NOTE: We avoid real GeoPandas geometry and spatial ops; tests that need
    geospatial behavior will patch gpd.read_file / gpd.sjoin explicitly.
    """
    class FakeTransportZones:
        def __init__(self, cache_path):
            self.cache_path = cache_path

        def get(self):
            # Keep it simple and deterministic; geometry is not used by our patched flows
            return pd.DataFrame(
                {
                    "transport_zone_id": [1, 2],
                    "urban_unit_category": ["A", "B"],
                    "page_url": ["https://example.com/ds1", "https://example.com/ds2"],
                }
            )

    cache_path = tmp_path / "transport_zones.gpkg"
    return FakeTransportZones(cache_path=cache_path)


@pytest.fixture
def fake_population_asset(fake_transport_zones):
    """
    Tiny stand-in object that looks like an "asset" dependency.
    - .inputs contains {"transport_zones": fake_transport_zones}
    - .get() returns a DataFrame (or minimal object) as needed
    """
    class FakePopulationAsset:
        def __init__(self):
            self.inputs = {"transport_zones": fake_transport_zones}

        def get(self):
            return pd.DataFrame({"population": [100, 200]})

    return FakePopulationAsset()
