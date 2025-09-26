import os
import zipfile
from pathlib import Path
import pandas as pandas
from mobility.gtfs import GTFS

def create_valid_gtfs_zip_file(valid_zip_file_path: Path):
    valid_zip_file_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(valid_zip_file_path, "w") as zip_file:
        zip_file.writestr("agency.txt", "agency_id,agency_name\n1,Agency\n", compress_type=zipfile.ZIP_STORED)
        zip_file.writestr("blob.bin", os.urandom(4096), compress_type=zipfile.ZIP_STORED)

def create_invalid_zip_file(invalid_zip_file_path: Path):
    invalid_zip_file_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(invalid_zip_file_path, "w") as zip_file:
        zip_file.writestr("not_gtfs.txt", "hello")

def test_download_gtfs_files_filters_small_and_invalid(monkeypatch, fake_transport_zones):
    gtfs_instance = GTFS(fake_transport_zones)

    stops_dataframe = pandas.DataFrame({
        "page_url": ["https://example.com/dsA", "https://example.com/dsB", "https://example.com/dsC"]
    })

    downloads_directory = Path(os.environ["MOBILITY_PACKAGE_DATA_FOLDER"]) / "gtfs"
    small_zip_file_path = downloads_directory / "idSmall_small.zip"
    invalid_zip_file_path = downloads_directory / "idBad_invalid.zip"
    valid_zip_file_path = downloads_directory / "idGood_valid.zip"

    def fake_get_gtfs_urls_method():
        return pandas.DataFrame([
            {"title": "Dataset A", "page_url": "https://example.com/dsA", "gtfs_datagouv_id": "idSmall", "gtfs_url": "https://example.com/small", "gtfs_title": "small"},
            {"title": "Dataset B", "page_url": "https://example.com/dsB", "gtfs_datagouv_id": "idBad", "gtfs_url": "https://example.com/bad", "gtfs_title": "invalid"},
            {"title": "Dataset C", "page_url": "https://example.com/dsC", "gtfs_datagouv_id": "idGood", "gtfs_url": "https://example.com/good", "gtfs_title": "valid"},
        ])

    monkeypatch.setattr(GTFS, "get_gtfs_urls", staticmethod(fake_get_gtfs_urls_method), raising=True)

    def fake_download_file_function(requested_url, destination_path):
        destination_path = Path(destination_path)
        if "small" in requested_url:
            destination_path.write_bytes(b"tiny")  # < 1024 bytes
        elif "bad" in requested_url:
            create_invalid_zip_file(destination_path)
        elif "good" in requested_url:
            create_valid_gtfs_zip_file(destination_path)
        else:
            raise AssertionError("Unexpected URL in test")

    monkeypatch.setattr("mobility.gtfs.download_file", fake_download_file_function, raising=True)

    downloaded_files_path_list = gtfs_instance.download_gtfs_files(stops_dataframe)

    assert downloaded_files_path_list == [str(valid_zip_file_path)]
    assert valid_zip_file_path.suffix == ".zip"
    assert valid_zip_file_path.exists()
    assert small_zip_file_path.exists()
    assert invalid_zip_file_path.exists()
