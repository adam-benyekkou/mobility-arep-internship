from pathlib import Path
import pandas as pd

def test_get_insee_data_calls_prepare_when_files_missing(tmp_path, monkeypatch, parquet_stubs, import_get_insee_data):
    get_mod = import_get_insee_data

    module_path_dir = tmp_path / "mobility_pkg"
    module_path_dir.mkdir(parents=True, exist_ok=True)
    fake_module_file = module_path_dir / "get_insee_data.py"
    monkeypatch.setattr(get_mod, "__file__", str(fake_module_file), raising=False)
    monkeypatch.setattr(get_mod.os.path, "dirname", lambda p: str(module_path_dir), raising=False)
    monkeypatch.setattr(get_mod, "__file__", str(fake_module_file), raising=False)

    data_folder_path = module_path_dir / "data" / "insee"
    work = data_folder_path / "work"
    fac = data_folder_path / "facilities"
    work.mkdir(parents=True, exist_ok=True)
    fac.mkdir(parents=True, exist_ok=True)

    expected_paths = {
        work / "jobs.parquet",
        work / "active_population.parquet",
        fac / "shops.parquet",
        fac / "schools.parquet",
        fac / "admin_facilities.parquet",
        fac / "sport_facilities.parquet",
        fac / "care_facilities.parquet",
        fac / "show_facilities.parquet",
        fac / "museum.parquet",
        fac / "restaurants.parquet",
    }

    prepare_calls = {"job_active_population": 0, "facilities": 0}

    def fake_prepare_job_active_population(test=False):
        prepare_calls["job_active_population"] += 1

    def fake_prepare_facilities():
        prepare_calls["facilities"] += 1

    monkeypatch.setattr(get_mod, "prepare_job_active_population", fake_prepare_job_active_population, raising=True)
    monkeypatch.setattr(get_mod, "prepare_facilities", fake_prepare_facilities, raising=True)

    parquet_stubs.set_read_mapping({
        p: pd.DataFrame({"DEPCOM": ["001"], "sink_volume": [1]}).set_index("DEPCOM")
        for p in expected_paths
    })

    result = get_mod.get_insee_data(test=True)

    assert prepare_calls["job_active_population"] == 1
    assert prepare_calls["facilities"] == 1
    assert set(parquet_stubs.read_calls) == expected_paths

    expected_keys = {"jobs", "active_population", "shops", "schools", "admin",
                     "sport", "care", "show", "museum", "restaurant"}
    assert set(result.keys()) == expected_keys
    for dataframe in result.values():
        assert list(dataframe.columns) == ["sink_volume"]
        assert dataframe.index.name == "DEPCOM"
