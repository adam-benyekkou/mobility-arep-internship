from pathlib import Path
import pandas as pd
import pytest

try:
    import get_swiss_data as mod
except ModuleNotFoundError:  # package layout fallback
    from mobility import get_swiss_data as mod


def test_get_swiss_data_raises_if_expected_columns_missing(monkeypatch, tmp_path):
    """
    If 'Territoire' or 'Total' are missing in the active population input,
    the function should error clearly rather than silently producing wrong results.
    """
    monkeypatch.setattr(mod, "__file__", str(tmp_path / "root" / "get_swiss_data.py"), raising=False)

    def fake_read_csv(path, *args, **kwargs):
        return pd.DataFrame({"Commune": ["0101 Zurich"]})

    # Missing 'Territoire' causes an AttributeError when accessing .Territoire
    def fake_read_excel_missing_territoire(path, *args, **kwargs):
        return pd.DataFrame({"Total": [100]})

    monkeypatch.setattr(pd, "read_csv", fake_read_csv, raising=True)
    monkeypatch.setattr(pd, "read_excel", fake_read_excel_missing_territoire, raising=True)

    with pytest.raises(Exception):
        mod.get_swiss_data()

    # Now provide 'Territoire' but miss 'Total' -> KeyError when computing ACT
    def fake_read_excel_missing_total(path, *args, **kwargs):
        return pd.DataFrame({"Territoire": ["code: 0101 Zurich"]})

    monkeypatch.setattr(pd, "read_excel", fake_read_excel_missing_total, raising=True)

    with pytest.raises(Exception):
        mod.get_swiss_data()
