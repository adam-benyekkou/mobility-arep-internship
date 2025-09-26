def test_get_prefers_cached_when_hash_matches_and_file_exists(AssetImpl, simple_inputs, cache_file, tmp_path, monkeypatch):
    # Fix the hash so we can precreate the expected files before construction
    fixed_hash = "abc123"
    monkeypatch.setattr(AssetImpl, "compute_inputs_hash", lambda self: fixed_hash)

    # Precreate the cache file and the matching hash file
    expected_cache = cache_file.parent / f"{fixed_hash}-{cache_file.name}"
    expected_cache.write_bytes(b"dummy")
    expected_hash_file = expected_cache.with_suffix(".inputs-hash")
    expected_hash_file.write_text(fixed_hash)

    asset = AssetImpl(simple_inputs, cache_file)

    # With matching hash + file present, __init__ should call get_cached once
    assert asset.created == 0
    assert asset.cached == 1
    assert asset.cache_path == expected_cache
    assert asset.hash_path == expected_hash_file
