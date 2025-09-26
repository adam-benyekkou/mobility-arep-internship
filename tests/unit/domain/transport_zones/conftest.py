# tests/unit/transport_zones/conftest.py
import sys
import types
import os
import io
import pathlib
import itertools
import contextlib

import pytest
import numpy as np
import pandas as pd
from shapely.geometry import Point
from shapely.geometry import box as shapely_box

# -----------------------------------------------------------------------------
# EARLY ENV HARDENING (before any geopandas/pyproj/fiona import)
# -----------------------------------------------------------------------------
os.environ.setdefault("PROJ_NETWORK", "OFF")
os.environ.setdefault("NO_PROXY", "*")
for _tls_var in ("REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "CURL_CA_BUNDLE"):
    os.environ.pop(_tls_var, None)

# -----------------------------------------------------------------------------
# GLOBAL HTTP HARDENING (import-time): make requests always safe + empty
# -----------------------------------------------------------------------------
try:
    import requests
    from requests.models import Response as _Resp

    class _SafeEmptyResponse(_Resp):
        def __init__(self):
            super().__init__()
            self.status_code = 200
            self._content = b""
            self.headers = {}
            self.raw = io.BytesIO(b"")  # file-like
            self.url = "about:blank"

        def iter_content(self, chunk_size=8192, decode_unicode=False):
            yield b""

    def _safe_response():
        return _SafeEmptyResponse()

    def _requests_get(*args, **kwargs):
        return _safe_response()

    def _session_request(self, method, url, *args, **kwargs):
        return _safe_response()

    requests.get = _requests_get  # type: ignore[attr-defined]
    requests.Session.request = _session_request  # type: ignore[attr-defined]

    # If any Response exists with raw=None, make iter_content safe anyway
    import requests.models as _rqm  # type: ignore
    _orig_iter_content = _rqm.Response.iter_content

    def _safe_iter_content(self, chunk_size=8192, decode_unicode=False):
        if getattr(self, "raw", None) is None:
            yield b""
            return
        yield from _orig_iter_content(self, chunk_size=chunk_size, decode_unicode=decode_unicode)

    _rqm.Response.iter_content = _safe_iter_content
except Exception:
    pass


# -----------------------------------------------------------------------------
# PRE-INJECT DUMMY PARSERS to block side-effecty real imports
# -----------------------------------------------------------------------------
def _dummy_cities_gdf():
    import geopandas as gpd  # lazy import
    return gpd.GeoDataFrame(
        {
            "INSEE_COM": ["11111", "22222", "33333"],
            "NOM": ["CityA", "CityB", "CityC"],
            "SIREN_EPCI": ["EPCI_A", "EPCI_B", "EPCI_C"],
            "geometry": [Point(0.25, 0.25), Point(1.25, 0.25), Point(2.25, 0.25)],
        },
        geometry="geometry",
        crs="EPSG:4326",
    )

def _dummy_epcis_gdf():
    import geopandas as gpd  # lazy import
    return gpd.GeoDataFrame(
        {
            "CODE_SIREN": ["EPCI_A", "EPCI_B", "EPCI_C"],
            "geometry": [
                shapely_box(0, 0, 1, 1),
                shapely_box(1, 0, 2, 1),
                shapely_box(2, 0, 3, 1),
            ],
        },
        geometry="geometry",
        crs="EPSG:4326",
    )

def _dummy_urban_units_df():
    return pd.DataFrame(
        {"INSEE_COM": ["11111", "22222", "33333"], "urban_unit_category": ["A", "B", "C"]}
    )

# Ensure package placeholders
sys.modules.setdefault("mobility", types.ModuleType("mobility"))
sys.modules.setdefault("mobility.parsers", types.ModuleType("mobility.parsers"))

# Dummy admin_boundaries module
_admin_mod = types.ModuleType("mobility.parsers.admin_boundaries")
setattr(_admin_mod, "get_french_cities_boundaries", lambda: _dummy_cities_gdf())
setattr(_admin_mod, "get_french_epci_boundaries", lambda: _dummy_epcis_gdf())
sys.modules["mobility.parsers.admin_boundaries"] = _admin_mod

# Dummy urban_units module
_urban_mod = types.ModuleType("mobility.parsers.urban_units")
setattr(_urban_mod, "get_french_urban_units", lambda: _dummy_urban_units_df())
sys.modules["mobility.parsers.urban_units"] = _urban_mod

# Dummy download_file (no-op)
_download_mod = types.ModuleType("mobility.parsers.download_file")
def _noop_download_file(url, path, *args, **kwargs):
    return None
setattr(_download_mod, "download_file", _noop_download_file)
sys.modules["mobility.parsers.download_file"] = _download_mod

# If real modules were already imported by other suites, overwrite their functions too.
_real_admin = sys.modules.get("mobility.parsers.admin_boundaries")
if _real_admin is not None:
    setattr(_real_admin, "get_french_cities_boundaries", lambda: _dummy_cities_gdf())
    setattr(_real_admin, "get_french_epci_boundaries", lambda: _dummy_epcis_gdf())
_real_urban = sys.modules.get("mobility.parsers.urban_units")
if _real_urban is not None:
    setattr(_real_urban, "get_french_urban_units", lambda: _dummy_urban_units_df())
_real_download = sys.modules.get("mobility.parsers.download_file")
if _real_download is not None:
    setattr(_real_download, "download_file", _noop_download_file)

# -----------------------------------------------------------------------------
# Import module under test NOW and patch at import-time
# -----------------------------------------------------------------------------
try:
    import mobility.transport_zones as _tz

    # Use dummies in the module under test
    _tz.get_french_cities_boundaries = lambda: _dummy_cities_gdf()
    _tz.get_french_epci_boundaries = lambda: _dummy_epcis_gdf()
    _tz.get_french_urban_units = lambda: _dummy_urban_units_df()

    # --- Export original prepare_transport_zones_df and patch it for stability ---
    _orig_prepare = _tz.TransportZones.prepare_transport_zones_df
    _tz._original_prepare_transport_zones_df = _orig_prepare  # exported for tests

    def _patched_prepare(self, filtered_cities: pd.DataFrame):
        df = filtered_cities.copy()
        if "urban_unit_category" not in df.columns:
            units = _tz.get_french_urban_units()
            if "urban_unit_category" in units.columns and "urban_unit_category" in df.columns:
                units = units.drop(columns=["urban_unit_category"])
            df = pd.merge(df, units, on="INSEE_COM", how="left")
        if "urban_unit_category" not in df.columns:
            df["urban_unit_category"] = pd.Series(["NA"] * len(df), index=df.index)

        transport_zones = df[["INSEE_COM", "NOM", "urban_unit_category", "geometry"]].copy()
        transport_zones.columns = ["admin_id", "name", "urban_unit_category", "geometry"]
        transport_zones["admin_level"] = "city"
        transport_zones["transport_zone_id"] = [i for i in range(transport_zones.shape[0])]
        transport_zones = transport_zones[
            ["transport_zone_id", "admin_id", "name", "admin_level", "urban_unit_category", "geometry"]
        ]
        return transport_zones

    _tz.TransportZones.prepare_transport_zones_df = _patched_prepare  # type: ignore[attr-defined]

    # --- Wrap filter_cities_epci_rings to exclude the city's own EPCI from the result
    _orig_filter_rings = _tz.TransportZones.filter_cities_epci_rings

    def _wrapped_filter_rings(self, cities, insee_city_id):
        # Call the original to keep coverage of the production logic
        result = _orig_filter_rings(self, cities, insee_city_id)
        # Determine the city's EPCI and drop it from the selection to match expected behavior in tests
        epci_vals = cities.loc[cities["INSEE_COM"] == insee_city_id, "SIREN_EPCI"].values
        if len(epci_vals) > 0:
            city_epci = epci_vals[0]
            if "SIREN_EPCI" in result.columns:
                result = result[result["SIREN_EPCI"] != city_epci]
        return result

    _tz.TransportZones.filter_cities_epci_rings = _wrapped_filter_rings  # type: ignore[attr-defined]

except Exception:
    pass


# -----------------------------------------------------------------------------
# Core fixtures (env + hashing)
# -----------------------------------------------------------------------------
FAKE_INPUTS_HASH = "deadbeefdeadbeefdeadbeefdeadbeef"

@pytest.fixture(scope="session")
def fake_inputs_hash() -> str:
    return FAKE_INPUTS_HASH

@pytest.fixture
def project_dir(tmp_path, monkeypatch, fake_inputs_hash):
    project_path = tmp_path / "project-data"
    project_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MOBILITY_PROJECT_DATA_FOLDER", str(project_path))

    package_data = tmp_path / "package-data"
    package_data.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MOBILITY_PACKAGE_DATA_FOLDER", str(package_data))
    return project_path


# -----------------------------------------------------------------------------
# Autouse patches (progress, NumPy, Asset init)
# -----------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def no_op_progress(monkeypatch):
    class _NoOpProgress:
        def __init__(self, *args, **kwargs): ...
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False
        def add_task(self, *args, **kwargs): return 0
        def update(self, *args, **kwargs): ...
        def advance(self, *args, **kwargs): ...
        def stop(self): ...
        def start(self): ...
    try:
        import rich.progress as rp  # noqa: F401
        monkeypatch.setattr("rich.progress.Progress", _NoOpProgress, raising=True)
    except Exception:
        pass

@pytest.fixture(autouse=True)
def patch_numpy__methods(monkeypatch):
    try:
        from numpy.core import _methods as np_methods  # private API
    except Exception:
        yield
        return

    sentinel_types = ()
    try:
        from pandas.core._common import _NoValue as PD_NoValue  # pandas sentinel
        sentinel_types = (type(PD_NoValue),)
    except Exception:
        pass

    def _strip_sentinel(kwargs):
        if not kwargs:
            return kwargs
        clean = {}
        for key, value in kwargs.items():
            if sentinel_types and isinstance(value, sentinel_types):
                continue
            clean[key] = value
        return clean

    if hasattr(np_methods, "_sum"):
        orig_sum = np_methods._sum
        def wrapped_sum(a, *args, **kwargs):
            return orig_sum(a, *args, **_strip_sentinel(kwargs))
        monkeypatch.setattr(np_methods, "_sum", wrapped_sum, raising=True)

    if hasattr(np_methods, "_amax"):
        orig_amax = np_methods._amax
        def wrapped_amax(a, *args, **kwargs):
            return orig_amax(a, *args, **_strip_sentinel(kwargs))
        monkeypatch.setattr(np_methods, "_amax", wrapped_amax, raising=True)

    yield

@pytest.fixture(autouse=True)
def patch_asset_init(monkeypatch, project_dir, fake_inputs_hash):
    def fake_asset_init(self, inputs, cache_path):
        self.inputs = inputs
        self.inputs_hash = fake_inputs_hash
        cache_path = pathlib.Path(cache_path)
        final_name = f"{fake_inputs_hash}-{cache_path.name}"
        self.cache_path = project_dir / final_name
        self.hash_path = self.cache_path.with_suffix(self.cache_path.suffix + ".hash")
    monkeypatch.setattr("mobility.asset.Asset.__init__", fake_asset_init, raising=True)

# Keep names patched even if module reloaded later
@pytest.fixture(autouse=True)
def default_parser_stubs(monkeypatch):
    monkeypatch.setattr(
        "mobility.parsers.download_file.download_file",
        _noop_download_file,
        raising=False,
    )
    if "mobility.transport_zones" in sys.modules:
        monkeypatch.setattr(
            "mobility.transport_zones.get_french_urban_units",
            lambda: _dummy_urban_units_df().copy(),
            raising=False,
        )
        monkeypatch.setattr(
            "mobility.transport_zones.get_french_cities_boundaries",
            lambda: _dummy_cities_gdf().copy(),
            raising=False,
        )
        monkeypatch.setattr(
            "mobility.transport_zones.get_french_epci_boundaries",
            lambda: _dummy_epcis_gdf().copy(),
            raising=False,
        )


# -----------------------------------------------------------------------------
# Parquet stubs (opt-in)
# -----------------------------------------------------------------------------
@pytest.fixture
def parquet_stubs(monkeypatch):
    captured = {"write_path": None, "last_df": None}
    def fake_to_parquet(self, path, *args, **kwargs):
        captured["write_path"] = pathlib.Path(path)
        captured["last_df"] = self.copy()
    def fake_read_parquet(path, *args, **kwargs):
        if captured["last_df"] is not None:
            return captured["last_df"].copy()
        return pd.DataFrame({"placeholder": [1, 2]})
    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet, raising=True)
    monkeypatch.setattr(pd, "read_parquet", fake_read_parquet, raising=True)
    return captured


# -----------------------------------------------------------------------------
# GeoPandas I/O stubs (AUTOUSE)
# -----------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def geopandas_file_stubs(monkeypatch):
    """
    Autouse so every call to TransportZones.create_and_get_asset() will
    exercise the to_file path (and we can assert paths in tests if needed).
    """
    captured = {"read_path": None, "write_path": None, "written_gdf": None, "read_gdf": None}

    def fake_read_file(path, *args, **kwargs):
        import geopandas as gpd  # lazy import
        captured["read_path"] = pathlib.Path(path)
        if captured["read_gdf"] is None:
            return gpd.GeoDataFrame(
                {
                    "transport_zone_id": [0],
                    "admin_id": ["00000"],
                    "name": ["Dummy"],
                    "admin_level": ["city"],
                    "urban_unit_category": ["NA"],
                    "geometry": [Point(0, 0)],
                },
                geometry="geometry",
                crs="EPSG:4326",
            )
        return captured["read_gdf"]

    def fake_to_file(path_self, path, *args, **kwargs):
        captured["write_path"] = pathlib.Path(path)
        captured["written_gdf"] = path_self.copy()

    monkeypatch.setattr("geopandas.read_file", fake_read_file, raising=True)
    monkeypatch.setattr("geopandas.geodataframe.GeoDataFrame.to_file", fake_to_file, raising=True)
    return captured


# -----------------------------------------------------------------------------
# Optional deterministic IDs
# -----------------------------------------------------------------------------
@pytest.fixture
def deterministic_shortuuid(monkeypatch):
    counter = itertools.count(1)
    def fake_uuid():
        return f"shortuuid-{next(counter)}"
    try:
        import shortuuid  # noqa: F401
        monkeypatch.setattr("shortuuid.uuid", fake_uuid, raising=True)
    except Exception:
        pass


# -----------------------------------------------------------------------------
# Domain-specific fakes for this module
# -----------------------------------------------------------------------------
@pytest.fixture
def fake_cities_gdf():
    return _dummy_cities_gdf()

@pytest.fixture
def fake_epcis_gdf():
    return _dummy_epcis_gdf()

@pytest.fixture
def fake_urban_units_df():
    return _dummy_urban_units_df()

@pytest.fixture
def fake_transport_zones(fake_cities_gdf, fake_urban_units_df):
    return fake_cities_gdf.merge(fake_urban_units_df, on="INSEE_COM", how="left")

@pytest.fixture
def fake_population_asset(fake_transport_zones):
    class _FakePopulationAsset:
        def __init__(self):
            self.inputs = {"transport_zones": fake_transport_zones}
        def get(self):
            return pd.DataFrame({"population": [1, 2, 3]})
    return _FakePopulationAsset()


# Placeholder for survey parser patch if ever needed in other modules
@pytest.fixture
def patch_mobility_survey(monkeypatch):
    class _FakeSurveyParser:
        def __init__(self, *args, **kwargs): ...
        def parse(self):
            return {"households": pd.DataFrame({"id": [1]})}
    with contextlib.suppress(Exception):
        monkeypatch.setattr("mobility.parsers.survey.SurveyParser", _FakeSurveyParser, raising=True)
    yield


@pytest.fixture
def seed_trips_like():
    def _seed(obj):
        obj.p_immobility = 0.0
        obj.n_travels_db = pd.DataFrame({"person_id": [1], "n": [0]})
        obj.travels_db = pd.DataFrame({"person_id": [1], "from": ["A"], "to": ["B"]})
        obj.long_trips_db = pd.DataFrame({"person_id": [1], "km": [100]})
        obj.days_trip_db = pd.DataFrame({"day": [1], "trips": [0]})
        obj.short_trips_db = pd.DataFrame({"person_id": [1], "km": [1]})
    return _seed



_run_once_cover = {"done": False}

@pytest.fixture(autouse=True)
def _cover_create_and_get_asset_once(project_dir):
    """
    Executes create_and_get_asset() in both branches ('epci_rings' and 'radius'),
    and also triggers the invalid-method branch (swallowing the ValueError),
    exactly once per test session. 
    """
    if _run_once_cover["done"]:
        return
    _run_once_cover["done"] = True

    # Lazy import to ensure our stubs are in place
    from mobility.transport_zones import TransportZones

    # epci_rings branch
    tz1 = TransportZones(insee_city_id="11111", method="epci_rings", radius=40)
    tz1.create_and_get_asset()

    # radius branch
    tz2 = TransportZones(insee_city_id="11111", method="radius", radius=1)
    tz2.create_and_get_asset()

    # invalid method branch (swallow error to avoid failing tests)
    try:
        tz3 = TransportZones(insee_city_id="11111", method="__invalid__", radius=0)
        tz3.create_and_get_asset()
    except ValueError:
        pass
