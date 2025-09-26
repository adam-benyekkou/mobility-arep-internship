from pathlib import Path
import pandas as pd

def test_get_insee_data_reads_cached_only_when_all_present(
    tmp_path, monkeypatch, parquet_stubs, import_get_insee_data
):
    get_mod = import_get_insee_data

    module_path_dir = tmp_path / "mobility_pkg2"
    module_path_dir.mkdir(parents=True, exist_ok=True)
    fake_module_file = module_path_dir / "get_insee_data.py"
    # Force the module’s dirname(__file__) to point to our tmp folder
    monkeypatch.setattr(get_mod.os.path, "dirname", lambda p: str(module_path_dir), raising=False)
    monkeypatch.setattr(get_mod, "__file__", str(fake_module_file), raising=False)

    data_folder_path = module_path_dir / "data" / "insee"
    work = data_folder_path / "work"
    fac = data_folder_path / "facilities"
    work.mkdir(parents=True, exist_ok=True)
    fac.mkdir(parents=True, exist_ok=True)

    # IMPORTANT: include malls.parquet for the existence gate
    expected_files = [
        work / "jobs.parquet",
        work / "active_population.parquet",
        fac / "malls.parquet",
        fac / "shops.parquet",
        fac / "schools.parquet",
        fac / "admin_facilities.parquet",
        fac / "sport_facilities.parquet",
        fac / "care_facilities.parquet",
        fac / "show_facilities.parquet",
        fac / "museum.parquet",
        fac / "restaurants.parquet",
    ]
    for p in expected_files:
        p.touch()

    parquet_stubs.set_read_mapping({
        p: pd.DataFrame({"DEPCOM": ["900"], "sink_volume": [42]}).set_index("DEPCOM")
        for p in expected_files
    })

    # If prepare_* get called in cached state, that is a bug — make them fail loudly
    def fail_prepare(*_args, **_kwargs):
        raise AssertionError("prepare_* should not be called when all cached files exist")

    monkeypatch.setattr(get_mod, "prepare_job_active_population", fail_prepare, raising=True)
    monkeypatch.setattr(get_mod, "prepare_facilities", fail_prepare, raising=True)

    result = get_mod.get_insee_data(test=False)

    # All parquet paths the module actually reads should be in read_calls
    # (malls.parquet is not read by the function, just checked for existence)
    assert set(parquet_stubs.read_calls) == set(expected_files) - {fac / "malls.parquet"}

    expected_keys = {"jobs", "active_population", "shops", "schools", "admin",
                     "sport", "care", "show", "museum", "restaurant"}
    assert set(result.keys()) == expected_keys
    assert list(result["jobs"].columns) == ["sink_volume"]
    assert result["schools"]["sink_volume"].iloc[0] == 42
