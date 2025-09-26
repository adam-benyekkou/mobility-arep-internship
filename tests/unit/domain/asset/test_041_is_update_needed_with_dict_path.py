def test_is_update_needed_with_dict_paths(AssetImpl, simple_inputs, dict_cache_files, tmp_path, monkeypatch):
    # Deterministic hash
    fixed_hash = "hh"
    monkeypatch.setattr(AssetImpl, "compute_inputs_hash", lambda self: fixed_hash)

    # Precreate BOTH rewritten cache files so "file_exists" is True
    rewritten = {k: p.parent / f"{fixed_hash}-{p.name}" for k, p in dict_cache_files.items()}
    for p in rewritten.values():
        p.write_bytes(b"x")

    # The .inputs-hash file lives next to the *first* rewritten path (based on dict insertion order)
    first_key = list(rewritten.keys())[0]
    hash_file = rewritten[first_key].with_suffix(".inputs-hash")
    hash_file.write_text(fixed_hash)

    asset = AssetImpl(simple_inputs, dict_cache_files)

    # On construction, with matching hash + all files existing, we should use cached
    assert asset.created == 0
    assert asset.cached == 1

    # Now remove one of the files -> update needed
    next(iter(rewritten.values())).unlink()
    assert asset.is_update_needed() is True
