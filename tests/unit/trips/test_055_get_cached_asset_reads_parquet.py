# tests/unit/trips/test_055_get_cached_asset_reads_parquet.py
import pandas as pd

def test_get_cached_asset_reads_parquet(monkeypatch, fake_population, patch_mobility_survey):
    import mobility.trips as mod

    called = {}

    def fake_read_parquet(path, *a, **k):
        called["path"] = str(path)
        return pd.DataFrame({"ok": [1]})

    monkeypatch.setattr(pd, "read_parquet", fake_read_parquet, raising=True)

    trips = mod.Trips(fake_population)

    out = trips.get_cached_asset()
    assert "ok" in out.columns
    # IMPORTANT: cache filename has a deterministic hash prefix (deadbeef-...)
    assert called["path"] == str(trips.cache_path)
