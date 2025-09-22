import json
import hashlib
from pathlib import Path

from mobility.asset import Asset


class StubNestedAsset(Asset):
    """
    A stub that *is* an Asset (so isinstance(..., Asset) is True) but we don't
    run its real parent __init__. We only need get_cached_hash to return a stable
    value for hashing tests.
    """
    def __init__(self, value="NESTED"):
        # Don't call super().__init__
        self._value = value
        self.inputs = {}
        self.cache_path = Path(".")
        self.hash_path = Path(".hash")

    def get_cached_hash(self):
        return self._value

    # Unused abstract implementations:
    def get_cached_asset(self): return None
    def create_and_get_asset(self): return None


def test_compute_inputs_hash_includes_nested_asset_hash(AssetImpl, cache_file):
    nested = StubNestedAsset("NESTEDHASH")
    inputs = {"a": 1, "b": nested}

    # Construct an instance (its own __init__ will call get; that's fine)
    asset = AssetImpl(inputs, cache_file)

    # Recompute to assert logic, not relying on value set in __init__
    computed = asset.compute_inputs_hash()

    # Expected hash is md5(json.dumps({"a":1,"b":"NESTEDHASH"}, sort_keys=True).encode())
    hashable_inputs = {"a": 1, "b": "NESTEDHASH"}
    expected = hashlib.md5(json.dumps(hashable_inputs, sort_keys=True).encode("utf-8")).hexdigest()

    assert computed == expected
