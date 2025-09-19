import os
from pathlib import Path

def test_setup_package_data_folder_path_default_yes_creates(mod, monkeypatch, tmp_path):

    # Home points to tmp
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    default_path = tmp_path / ".mobility" / "data"

    # Simulate user typing "yes"
    monkeypatch.setattr("builtins.input", lambda prompt="": "yes")

    created = {}
    def fake_makedirs(path, *a, **k):
        created["path"] = str(path)
    monkeypatch.setattr(os, "makedirs", fake_makedirs)

    # Ensure it doesn't exist so default branch runs
    assert not default_path.exists()

    mod.setup_package_data_folder_path(None)

    assert os.environ["MOBILITY_PACKAGE_DATA_FOLDER"] == str(default_path)
    assert created["path"] == str(default_path)
