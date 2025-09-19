import os
from pathlib import Path

def test_setup_package_data_folder_path_with_custom_path(mod, monkeypatch, tmp_path):

    custom_path = tmp_path / "pkg_data"
    created = {}

    def fake_makedirs(path, *a, **k):
        created["path"] = str(path)

    monkeypatch.setattr(os, "makedirs", fake_makedirs)

    # Path does not exist -> makedirs called
    assert not custom_path.exists()
    mod.setup_package_data_folder_path(str(custom_path))
    assert os.environ["MOBILITY_PACKAGE_DATA_FOLDER"] == str(custom_path)
    assert created["path"] == str(custom_path)
