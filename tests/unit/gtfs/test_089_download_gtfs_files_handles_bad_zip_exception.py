import os
from pathlib import Path
import pandas as pandas

from mobility.gtfs import GTFS

def test_download_gtfs_files_handles_bad_zip_exception(monkeypatch, fake_transport_zones):
    gtfs_instance = GTFS(fake_transport_zones)

    stops_dataframe = pandas.DataFrame({"page_url": ["https://example.com/dsBadZip"]})
    downloads_directory = Path(os.environ["MOBILITY_PACKAGE_DATA_FOLDER"]) / "gtfs"
    corrupt_zip_file = downloads_directory / "idCorrupt_corrupt.zip"

    def fake_get_gtfs_urls():
        return pandas.DataFrame([{
            "title": "Dataset X",
            "page_url": "https://example.com/dsBadZip",
            "gtfs_datagouv_id": "idCorrupt",
            "gtfs_url": "https://example.com/corrupt",
            "gtfs_title": "corrupt",
        }])
    monkeypatch.setattr(GTFS, "get_gtfs_urls", staticmethod(fake_get_gtfs_urls), raising=True)

    def fake_download_file(url, path):
        Path(path).write_bytes(os.urandom(4096))
    monkeypatch.setattr("mobility.gtfs.download_file", fake_download_file, raising=True)

    downloaded_files_list = gtfs_instance.download_gtfs_files(stops_dataframe)

    assert downloaded_files_list == []
    assert corrupt_zip_file.exists()
