def test_update_hash_and_get_cached_hash(AssetImpl, simple_inputs, cache_file, monkeypatch):
    monkeypatch.setattr(AssetImpl, "compute_inputs_hash", lambda self: "zzz")

    asset = AssetImpl(simple_inputs, cache_file)

    # Initially there's a hash written during __init__ (after create)
    initial_hash = asset.get_cached_hash()
    assert initial_hash == "zzz"

    # Update the hash and check it's persisted and reflected in memory
    asset.update_hash("newhash")
    assert asset.inputs_hash == "newhash"
    assert asset.get_cached_hash() == "newhash"
