# conftest.py
import os
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# -------------------------
# Project / environment
# -------------------------
@pytest.fixture()
def project_dir(tmp_path, monkeypatch):
    tmp_dir = tmp_path / "mobility_project"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MOBILITY_PROJECT_DATA_FOLDER", str(tmp_dir))
    monkeypatch.setenv("MOBILITY_PACKAGE_DATA_FOLDER", str(tmp_dir / "pkgdata"))
    return tmp_dir


# -------------------------
# Robust module loader for mobility.get_insee_data
# -------------------------
@pytest.fixture
def import_get_insee_data():
    """
    Try: import mobility.get_insee_data
    Else: load from mobility/get_insee_data.py or ./get_insee_data.py and register as mobility.get_insee_data.
    """
    import sys, types, importlib.util
    try:
        import mobility.get_insee_data as mod  # type: ignore
        return mod
    except ModuleNotFoundError:
        pass

    # Ensure parent package exists so submodule can be registered
    sys.modules.setdefault("mobility", types.ModuleType("mobility"))

    candidate_paths = [
        Path.cwd() / "mobility" / "get_insee_data.py",
        Path.cwd() / "get_insee_data.py",
    ]
    for candidate in candidate_paths:
        if candidate.exists():
            spec = importlib.util.spec_from_file_location("mobility.get_insee_data", candidate)
            module = importlib.util.module_from_spec(spec)
            sys.modules["mobility.get_insee_data"] = module
            assert spec and spec.loader
            spec.loader.exec_module(module)  # type: ignore[attr-defined]
            return module

    raise ModuleNotFoundError(
        "Could not import mobility.get_insee_data or locate get_insee_data.py "
        f"in {candidate_paths}"
    )


# -------------------------
# Asset init patch (generic)
# -------------------------
@pytest.fixture(autouse=True)
def patch_asset_init(monkeypatch, project_dir):
    fake_inputs_hash = "deadbeefdeadbeefdeadbeefdeadbeef"

    def fake_init(self, inputs=None, filename="asset.parquet", **_kwargs):
        self.inputs = inputs or {}
        self.inputs_hash = fake_inputs_hash
        cache_file = f"{fake_inputs_hash}-{filename}"
        self.cache_path = Path(os.environ.get("MOBILITY_PROJECT_DATA_FOLDER", ".")) / cache_file
        self.hash_path = self.cache_path

    try:
        import mobility.asset  # may not exist; ignore if missing
        monkeypatch.setattr(mobility.asset.Asset, "__init__", fake_init, raising=False)  # type: ignore
    except Exception:
        pass

    patch_asset_init.fake_inputs_hash = fake_inputs_hash
    return patch_asset_init


# -------------------------
# No-op rich progress
# -------------------------
@pytest.fixture(autouse=True)
def no_op_progress(monkeypatch):
    class _NoOpProgress:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False
        def add_task(self, *args, **kwargs): return 0
        def update(self, *args, **kwargs): pass
        def advance(self, *args, **kwargs): pass
        def stop(self): pass

    try:
        import rich.progress
        monkeypatch.setattr(rich.progress, "Progress", _NoOpProgress, raising=False)
    except Exception:
        pass


# -------------------------
# NumPy _methods wrappers
# -------------------------
@pytest.fixture(autouse=True)
def patch_numpy__methods(monkeypatch):
    try:
        from numpy.core import _methods as np_methods  # type: ignore
    except Exception:
        yield
        return

    def _strip_no_value(args, kwargs):
        _noval = getattr(np, "_NoValue", object())
        args = tuple(a for a in args if a is not _noval)
        kwargs = {k: v for k, v in (kwargs or {}).items() if v is not _noval}
        return args, kwargs

    original_sum = getattr(np_methods, "_sum", None)
    original_amax = getattr(np_methods, "_amax", None)

    if original_sum is not None:
        def wrapped_sum(*args, **kwargs):
            a2, k2 = _strip_no_value(args, kwargs)
            return original_sum(*a2, **(k2 or {}))
        monkeypatch.setattr(np_methods, "_sum", wrapped_sum, raising=False)

    if original_amax is not None:
        def wrapped_amax(*args, **kwargs):
            a2, k2 = _strip_no_value(args, kwargs)
            return original_amax(*a2, **(k2 or {}))
        monkeypatch.setattr(np_methods, "_amax", wrapped_amax, raising=False)

    yield


# -------------------------
# Parquet stubs
# -------------------------
@pytest.fixture
def parquet_stubs(monkeypatch):
    class _ParquetStub:
        def __init__(self):
            self.read_mapping = {}
            self.read_calls = []
            self.write_calls = []

        def set_read_mapping(self, mapping: dict):
            self.read_mapping = {Path(k): v for k, v in mapping.items()}

        def read_parquet(self, path, *args, **kwargs):
            p = Path(path)
            self.read_calls.append(p)
            if p in self.read_mapping:
                return self.read_mapping[p]
            return pd.DataFrame({"DEPCOM": [], "sink_volume": []}).set_index("DEPCOM")

        def to_parquet(self, df, path, *args, **kwargs):
            p = Path(path)
            self.write_calls.append(p)
            return df

    stub = _ParquetStub()

    monkeypatch.setattr(pd, "read_parquet", stub.read_parquet, raising=False)

    def _df_to_parquet(self, path, *args, **kwargs):
        return stub.to_parquet(self, path, *args, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "to_parquet", _df_to_parquet, raising=False)

    return stub


# -------------------------
# shortuuid deterministic (optional)
# -------------------------
@pytest.fixture
def deterministic_shortuuid(monkeypatch):
    counter = {"n": 0}
    def fake_uuid():
        counter["n"] += 1
        return f"shortuuid-{counter['n']:04d}"
    try:
        import shortuuid  # type: ignore
        monkeypatch.setattr(shortuuid, "uuid", fake_uuid, raising=False)
    except Exception:
        pass
    return fake_uuid


# -------------------------
# Minimal helpers
# -------------------------
@pytest.fixture
def fake_transport_zones():
    return pd.DataFrame(
        {
            "transport_zone_id": ["001", "002"],
            "urban_unit_category": ["urban", "rural"],
            "geometry": [None, None],
        }
    )

@pytest.fixture
def fake_population_asset(fake_transport_zones):
    class _PopAsset:
        def __init__(self):
            self.inputs = {"transport_zones": fake_transport_zones}
        def get(self):
            return pd.DataFrame(
                {"DEPCOM": ["001", "002"], "population": [100, 50]}
            ).set_index("DEPCOM")
    return _PopAsset()

@pytest.fixture
def patch_mobility_survey(monkeypatch):
    class _FakeSurveyParser:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
        def parse(self):
            return {
                "individuals": pd.DataFrame({"person_id": [1, 2], "age": [30, 40]}),
                "trips": pd.DataFrame({"person_id": [1, 1, 2], "distance_km": [1.0, 2.0, 3.0]}),
            }
    try:
        import mobility.parsers.surveys  # type: ignore
        monkeypatch.setattr(mobility.parsers.surveys, "SurveyParser", _FakeSurveyParser, raising=False)
    except Exception:
        pass
    return _FakeSurveyParser
