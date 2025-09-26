from pathlib import Path
import pandas as pd
import pytest

try:
    import get_swiss_data as mod
except ModuleNotFoundError:  # package layout fallback
    from mobility import get_swiss_data as mod


def test_get_swiss_data_constructs_expected_local_paths(monkeypatch, tmp_path, capsys):
    # Arrange: place the module's __file__ inside a fake package directory within tmp_path
    fake_pkg_dir = tmp_path / "pkg"
    fake_pkg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(mod, "__file__", str(fake_pkg_dir / "get_swiss_data.py"), raising=False)

    # Capture the paths that pandas loaders receive
    read_calls = {"csv_paths": [], "excel_paths": []}

    def fake_read_csv(path, *args, **kwargs):
        read_calls["csv_paths"].append(Path(path))
        # Minimal dataframe matching code expectations: 'Commune' has "Code Name"
        return pd.DataFrame({"Commune": ["0101 Zurich", "0202 Basel"]})

    def fake_read_excel(path, *args, **kwargs):
        read_calls["excel_paths"].append(Path(path))
        # Must include 'Territoire' and 'Total'
        return pd.DataFrame({"Territoire": ["code: 0101 Zurich", "code: 0202 Basel"], "Total": [100, 200]})

    monkeypatch.setattr(pd, "read_csv", fake_read_csv, raising=True)
    monkeypatch.setattr(pd, "read_excel", fake_read_excel, raising=True)

    # Act
    data = mod.get_swiss_data()

    # Assert: correct print
    out = capsys.readouterr().out
    assert "Getting local swiss data" in out

    # Assert: path construction matches <module_dir>/data/CH/<filename>
    expected_data_dir = Path(fake_pkg_dir) / "data" / "CH"
    expected_csv_path = expected_data_dir / "CH-2021-emplois-communes.csv"
    expected_excel_path = expected_data_dir / "CH-2022-population-communes.xlsx"

    assert len(read_calls["csv_paths"]) == 1
    assert len(read_calls["excel_paths"]) == 1
    assert read_calls["csv_paths"][0] == expected_csv_path
    assert read_calls["excel_paths"][0] == expected_excel_path

    # Assert returned keys exist
    assert set(data.keys()) == {"jobs", "active_population"}
