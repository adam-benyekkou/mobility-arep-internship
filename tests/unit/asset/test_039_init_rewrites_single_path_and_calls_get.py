from pathlib import Path


def test_init_rewrites_single_path_and_calls_get(AssetImpl, simple_inputs, cache_file, monkeypatch):
    # Force a deterministic hash so we can assert file names easily
    monkeypatch.setattr(AssetImpl, "compute_inputs_hash", lambda self: "hash123")

    asset = AssetImpl(simple_inputs, cache_file)

    # cache_path should be rewritten to include the hash prefix
    assert asset.cache_path == cache_file.parent / ("hash123-" + cache_file.name)
    # hash file path is derived from cache_path with .inputs-hash suffix
    assert asset.hash_path == asset.cache_path.with_suffix(".inputs-hash")

    # No cache file exists and no hash yet => create called once at __init__
    assert asset.created == 1
    assert asset.cached == 0
