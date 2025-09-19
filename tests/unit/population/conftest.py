# tests/unit/population/conftest.py
import pytest
import pandas as pd
import mobility.asset as asset_mod


# 1) Make Asset.__init__ harmless (so Population.__init__ via super() doesn't do real I/O)
@pytest.fixture(autouse=True)
def patch_asset_init(monkeypatch):
    def fake_init(self, inputs, cache_path):
        self.inputs = inputs
        self.cache_path = cache_path
    monkeypatch.setattr(asset_mod.Asset, "__init__", fake_init)


# 2) Put the project cache dir in a pytest temp folder
@pytest.fixture(autouse=True)
def temp_project_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("MOBILITY_PROJECT_DATA_FOLDER", str(tmp_path))


# 3) Replace rich.Progress with a no-op (avoids console/width internals)
@pytest.fixture(autouse=True)
def no_op_progress(monkeypatch):
    import mobility.population as module
    class ProgressNoOp:
        def __enter__(self): return self
        def __exit__(self, *exc): pass
        def add_task(self, *a, **k): return 1
        def update(self, *a, **k): pass
    monkeypatch.setattr(module, "Progress", ProgressNoOp)


# 4) Make pandas .sample() deterministic and tolerant (works for DF and Series)
@pytest.fixture(autouse=True)
def deterministic_sample(monkeypatch):
    def _count(obj, args, kwargs):
        # Prefer explicit n (positional or keyword) when it's an int/float
        if args:
            n = args[0]
            if isinstance(n, (int, float)):
                return max(1, int(n))
        if "n" in kwargs and isinstance(kwargs["n"], (int, float)):
            return max(1, int(kwargs["n"]))
        # Otherwise use frac if numeric; else default to 1
        frac = kwargs.get("frac", None)
        if isinstance(frac, (int, float)):
            # ceil(frac * len) but at least 1
            return max(1, int((frac * len(obj)) + 0.9999))
        return 1

    def df_sample(self, *args, **kwargs):
        return self.iloc[:_count(self, args, kwargs)].copy()

    def series_sample(self, *args, **kwargs):
        # Convert Series to one-row-per-item DataFrame, reuse logic, squeeze back
        df = self.to_frame().T if self.ndim == 1 else self.to_frame()
        out = df.iloc[:_count(df, args, kwargs)].copy()
        return out.squeeze()

    monkeypatch.setattr(pd.DataFrame, "sample", df_sample, raising=True)
    monkeypatch.setattr(pd.Series,   "sample", series_sample, raising=True)


# 5) Minimal shared fixtures used by tests
@pytest.fixture
def transport_zones_dataframe():
    return pd.DataFrame({
        "admin_id": ["C1", "C2"],
        "transport_zone_id": [101, 102],
        "geometry": [None, None],  # geometry not used; sjoin is stubbed in tests
    })


class FakeTransportZonesAsset:
    """Tiny stand-in that mimics an asset with .get() -> DataFrame."""
    def __init__(self, dataframe): self._dataframe = dataframe
    def get(self): return self._dataframe


@pytest.fixture
def fake_transport_zones_asset(transport_zones_dataframe):
    return FakeTransportZonesAsset(transport_zones_dataframe)
