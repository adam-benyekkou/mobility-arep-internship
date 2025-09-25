import json
from pathlib import Path
import pandas as pandas
from mobility.gtfs import GTFS

def test_get_gtfs_urls_parses_metadata_and_returns_dataframe(monkeypatch, project_dir, fake_transport_zones):
    gtfs_instance = GTFS(fake_transport_zones)

    written_metadata_path_holder = {}

    def fake_download_file_function(requested_url, destination_path):
        metadata_content = [
            {
                "title": "Dataset A",
                "page_url": "https://example.com/dsA",
                "resources": [
                    {"format": "GTFS", "datagouv_id": "idA", "original_url": "https://example.com/dsA.zip", "title": "Agtfs"},
                    {"format": "OTHER", "datagouv_id": "idA2", "original_url": "https://example.com/dsA2", "title": "Other"},
                ],
            },
            {
                "title": "Dataset B",
                "page_url": "https://example.com/dsB",
                "resources": [
                    {"format": "GTFS", "datagouv_id": "idB", "original_url": "https://example.com/dsB.zip", "title": "Bgtfs"},
                ],
            },
        ]
        destination_path = Path(destination_path)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with open(destination_path, "w", encoding="utf-8") as output_file:
            json.dump(metadata_content, output_file)
        written_metadata_path_holder["path"] = destination_path

    monkeypatch.setattr("mobility.gtfs.download_file", fake_download_file_function, raising=True)

    metadata_dataframe = gtfs_instance.get_gtfs_urls()

    assert list(metadata_dataframe.columns) == ["title", "page_url", "gtfs_datagouv_id", "gtfs_url", "gtfs_title"]
    assert set(metadata_dataframe["page_url"]) == {"https://example.com/dsA", "https://example.com/dsB"}
    assert len(metadata_dataframe) == 2
    assert written_metadata_path_holder["path"].name == "gtfs_metadata.json"
