import os
from pathlib import Path
import pandas as pandas

from mobility.gtfs import GTFS

def test_get_stops_builds_when_missing(monkeypatch, project_dir, fake_transport_zones):
    gtfs_instance = GTFS(fake_transport_zones)

    gpkg_path = Path(os.environ["MOBILITY_PACKAGE_DATA_FOLDER"]) / "gtfs" / "all_gtfs_stops.gpkg"
    if gpkg_path.exists():
        gpkg_path.unlink()

    def fake_read_csv(csv_path):
        return pandas.DataFrame({
            "stop_lon": [2.1, 2.2],
            "stop_lat": [48.9, 48.8],
            "dataset_id": ["ds1", "ds2"],
        })
    monkeypatch.setattr("pandas.read_csv", fake_read_csv, raising=True)

    class FakeResponse:
        def __init__(self, url): self.url = url
    def fake_requests_get(url, allow_redirects=True):
        return FakeResponse(url)
    monkeypatch.setattr("mobility.gtfs.requests.get", fake_requests_get, raising=True)

    class FakeGeoDataFrame(pandas.DataFrame):
        _metadata = ["crs"]
        @property
        def _constructor(self): return FakeGeoDataFrame
        def to_crs(self, *args, **kwargs): return None
        def to_file(self, path): Path(path).write_bytes(b"gpkg")
        @property
        def crs(self): return getattr(self, "_crs", None)
        @crs.setter
        def crs(self, value): self._crs = value

    def fake_points_from_xy(x_values, y_values):
        return list(zip(x_values, y_values))

    def fake_geo_dataframe(dataframe, geometry=None):
        geo_dataframe = FakeGeoDataFrame(dataframe.copy())
        if geometry is not None:
            geo_dataframe["geometry"] = geometry
        return geo_dataframe

    def fake_spatial_join(left_dataframe, right_dataframe, how="inner", predicate="within"):
        result_dataframe = pandas.DataFrame(left_dataframe).copy()
        result_dataframe["joined_marker"] = "ok"
        return result_dataframe

    monkeypatch.setattr("mobility.gtfs.gpd.points_from_xy", fake_points_from_xy, raising=True)
    monkeypatch.setattr("mobility.gtfs.gpd.GeoDataFrame", fake_geo_dataframe, raising=True)
    monkeypatch.setattr("mobility.gtfs.gpd.sjoin", fake_spatial_join, raising=True)

    def fake_download_file(url, path):
        Path(path).write_text("dummy,content\n", encoding="utf-8")
    monkeypatch.setattr("mobility.gtfs.download_file", fake_download_file, raising=True)

    result_dataframe = gtfs_instance.get_stops(fake_transport_zones)

    assert isinstance(result_dataframe, pandas.DataFrame)
    assert "joined_marker" in result_dataframe.columns
    assert gpkg_path.exists()
