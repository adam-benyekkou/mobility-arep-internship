# tests/unit/asset/conftest.py
import pathlib
import pytest

from mobility.asset import Asset


class CountingAsset(Asset):
    """
    Minimal concrete Asset used in tests.
    Tracks whether create/get_cached were called and returns simple sentinels.
    """
    def __init__(self, inputs, cache_path):
        self.created = 0
        self.cached = 0
        super().__init__(inputs, cache_path)

    def get_cached_asset(self):
        self.cached += 1
        return "CACHED"

    def create_and_get_asset(self):
        self.created += 1
        return "CREATED"


@pytest.fixture
def AssetImpl():
    """
    Yields the CountingAsset class so tests can monkeypatch per-class methods
    (like compute_inputs_hash) safely without leaking across tests.
    """
    return CountingAsset


@pytest.fixture
def simple_inputs():
    # Keep inputs stable across tests; json sort_keys=True in the impl
    return {"a": 1, "b": 2}


@pytest.fixture
def cache_file(tmp_path):
    # A convenient original (pre-rewrite) cache filename to pass in
    return tmp_path / "result.bin"


@pytest.fixture
def dict_cache_files(tmp_path):
    # Two original (pre-rewrite) cache filenames for dict mode
    return {
        "part1": tmp_path / "p1.parquet",
        "part2": tmp_path / "p2.parquet",
    }
