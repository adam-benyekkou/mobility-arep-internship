import os

def test_setup_project_data_folder_path_with_custom_path(mod, monkeypatch, tmp_path):
    import mobility.set_params as mod

    custom_path = tmp_path / "proj_data"
    created = {}
    monkeypatch.setattr(os, "makedirs", lambda p, *a, **k: created.update(path=str(p)))

    mod.setup_project_data_folder_path(str(custom_path))
    assert os.environ["MOBILITY_PROJECT_DATA_FOLDER"] == str(custom_path)
    assert created["path"] == str(custom_path)
