import os
import pandas as pd

def test_get_cached_asset_reads_parquet(monkeypatch, project_dir):
    import mobility.transport_mode_choice_model as mod

    monkeypatch.setattr(mod.Asset, "get", lambda self: None, raising=True)
    model = mod.TransportModeChoiceModel(object(), cost_of_time=20.0)

    seen = {}
    def fake_read_parquet(path):
        seen["path"] = os.fspath(path)
        return pd.DataFrame({"ok": [1]})
    monkeypatch.setattr(pd, "read_parquet", fake_read_parquet, raising=True)

    out = model.get_cached_asset()

    assert seen["path"] == os.fspath(project_dir / "deadbeef-modal_choice_model.parquet")
    assert list(out.columns) == ["ok"]
