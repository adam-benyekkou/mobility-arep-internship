import os

def test_setup_project_data_folder_path_default_yes_creates(mod, monkeypatch, tmp_path):
    # Default depends on MOBILITY_PACKAGE_DATA_FOLDER
    package_path = tmp_path / ".mobility" / "data"
    projects_path = package_path / "projects"

    monkeypatch.setenv("MOBILITY_PACKAGE_DATA_FOLDER", str(package_path))
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")

    created = {}
    monkeypatch.setattr(os, "makedirs", lambda p, *a, **k: created.update(path=str(p)))

    assert not projects_path.exists()
    mod.setup_project_data_folder_path(None)

    assert os.environ["MOBILITY_PROJECT_DATA_FOLDER"] == str(projects_path)
    assert created["path"] == str(projects_path)
