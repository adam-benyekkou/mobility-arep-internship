from pathlib import Path
import pytest

def test_setup_package_data_folder_path_default_no_raises(mod, monkeypatch, tmp_path):

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr("builtins.input", lambda prompt="": "no")

    with pytest.raises(ValueError):
        mod.setup_package_data_folder_path(None)
