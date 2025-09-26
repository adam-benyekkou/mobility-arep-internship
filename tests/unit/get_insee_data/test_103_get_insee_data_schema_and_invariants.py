from pathlib import Path
import pandas as pd

def test_get_insee_data_schema_and_invariants(
    tmp_path, monkeypatch, parquet_stubs, import_get_insee_data
):
    get_mod = import_get_insee_data

    module_path_dir = tmp_path / "mobility_pkg3"
    module_path_dir.mkdir(parents=True, exist_ok=True)
    fake_module_file = module_path_dir / "get_insee_data.py"
    # Force dirname(__file__) to our tmp folder
    monkeypatch.setattr(get_mod.os.path, "dirname", lambda p: str(module_path_dir), raising=False)
    monkeypatch.setattr(get_mod, "__file__", str(fake_module_file), raising=False)

    data_folder_path = module_path_dir / "data" / "insee"
    work = data_folder_path / "work"
    fac = data_folder_path / "facilities"
    work.mkdir(parents=True, exist_ok=True)
    fac.mkdir(parents=True, exist_ok=True)

    # Include malls.parquet in the existence set
    file_map = {
        "jobs": work / "jobs.parquet",
        "active_population": work / "active_population.parquet",
        "malls": fac / "malls.parquet",  # existence check only; not read
        "shops": fac / "shops.parquet",
        "schools": fac / "schools.parquet",
        "admin": fac / "admin_facilities.parquet",
        "sport": fac / "sport_facilities.parquet",
        "care": fac / "care_facilities.parquet",
        "show": fac / "show_facilities.parquet",
        "museum": fac / "museum.parquet",
        "restaurant": fac / "restaurants.parquet",
    }
    for p in file_map.values():
        p.touch()

    # Mapping only for files that will be READ (skip malls)
    mapping = {}
    for key, path in file_map.items():
        if key == "malls":
            continue
        mapping[path] = pd.DataFrame(
            {"DEPCOM": ["001", "002"], "sink_volume": [1, 0] if key == "jobs" else [5, 10]}
        ).set_index("DEPCOM")
    parquet_stubs.set_read_mapping(mapping)

    result = get_mod.get_insee_data()

    expected_keys = {"jobs", "active_population", "shops", "schools", "admin",
                     "sport", "care", "show", "museum", "restaurant"}
    assert set(result.keys()) == expected_keys

    for df in result.values():
        assert df.index.name == "DEPCOM"
        assert list(df.columns) == ["sink_volume"]
        assert (df["sink_volume"] >= 0).all()
        assert pd.api.types.is_numeric_dtype(df["sink_volume"])
    assert result["jobs"].loc["001", "sink_volume"] == 1
