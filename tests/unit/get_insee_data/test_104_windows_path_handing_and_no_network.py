from pathlib import Path
import pandas as pd

def test_path_handling_uses_paths_not_strings(
    tmp_path, monkeypatch, parquet_stubs, import_get_insee_data
):
    get_mod = import_get_insee_data

    windows_like_root = tmp_path / "pkgwin"
    windows_like_root.mkdir(parents=True, exist_ok=True)
    fake_module_file = windows_like_root / "get_insee_data.py"
    # Force dirname(__file__) to our tmp folder
    monkeypatch.setattr(get_mod.os.path, "dirname", lambda p: str(windows_like_root), raising=False)
    monkeypatch.setattr(get_mod, "__file__", str(fake_module_file), raising=False)

    data_folder_path = windows_like_root / "data" / "insee"
    work = data_folder_path / "work"
    fac = data_folder_path / "facilities"
    work.mkdir(parents=True, exist_ok=True)
    fac.mkdir(parents=True, exist_ok=True)

    # Include malls.parquet for the existence gate
    files = [
        work / "jobs.parquet",
        work / "active_population.parquet",
        fac / "malls.parquet",  # existence check only; not read
        fac / "shops.parquet",
        fac / "schools.parquet",
        fac / "admin_facilities.parquet",
        fac / "sport_facilities.parquet",
        fac / "care_facilities.parquet",
        fac / "show_facilities.parquet",
        fac / "museum.parquet",
        fac / "restaurants.parquet",
    ]
    for p in files:
        p.touch()

    # Stub reads for only the files the function actually reads (exclude malls)
    read_files = [p for p in files if p.name != "malls.parquet"]
    parquet_stubs.set_read_mapping({
        p: pd.DataFrame({"DEPCOM": ["001"], "sink_volume": [1]}).set_index("DEPCOM")
        for p in read_files
    })

    result = get_mod.get_insee_data()

    assert set(parquet_stubs.read_calls) == set(read_files)
    assert "restaurant" in result
    assert result["restaurant"]["sink_volume"].iloc[0] == 1
