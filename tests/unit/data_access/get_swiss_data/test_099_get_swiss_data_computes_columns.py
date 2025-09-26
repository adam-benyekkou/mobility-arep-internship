from pathlib import Path
import pandas as pd
import numpy as np
import pytest

try:
    import get_swiss_data as mod
except ModuleNotFoundError:  # package layout fallback
    from mobility import get_swiss_data as mod


def test_get_swiss_data_builds_expected_columns_and_activity(monkeypatch, tmp_path):
    # Arrange module base path so path builds correctly (no actual disk I/O).
    monkeypatch.setattr(mod, "__file__", str(tmp_path / "modroot" / "get_swiss_data.py"), raising=False)

    def fake_read_csv(path, *args, **kwargs):
        # Jobs.Commune contains code and commune separated by space; function splits to Code and Commune
        return pd.DataFrame({"Commune": ["0101 Zurich", "0202 Basel", "0303 Bern"], "Other": [1, 2, 3]})

    def fake_read_excel(path, *args, **kwargs):
        # IMPORTANT: No space after the colon so that after split the first token is 'code:0101'
        # and Code.str.slice(6) -> '101' (index 6 is the second digit of '0101').
        return pd.DataFrame(
            {
                "Territoire": ["code:0101 Zurich", "code:0202 Basel", "code:0303 Bern"],
                "Total": [100, 250, 80],
            }
        )

    monkeypatch.setattr(pd, "read_csv", fake_read_csv, raising=True)
    monkeypatch.setattr(pd, "read_excel", fake_read_excel, raising=True)

    # Act
    swiss = mod.get_swiss_data()

    # Assert structure
    assert "jobs" in swiss and "active_population" in swiss

    jobs = swiss["jobs"]
    active = swiss["active_population"]

    # Jobs: Code and Commune columns created by split
    assert {"Code", "Commune"}.issubset(jobs.columns)
    assert jobs.loc[0, "Code"] == "0101"
    assert jobs.loc[0, "Commune"] == "Zurich"

    # Active population: Code and Commune split from Territoire, then Code sliced; ACT computed with constant
    assert {"Code", "Commune", "Total", "ACT"}.issubset(active.columns)
    # With no space after colon, slice(6) yields '101', '202', ...
    assert active.loc[0, "Code"] == "101"
    assert active.loc[1, "Code"] == "202"

    expected_rate = mod.SWISS_ACTIVITY_RATE
    np.testing.assert_allclose(active["ACT"].to_numpy(), (active["Total"] * expected_rate).to_numpy())

    # Spot-check without brittle full DataFrame equality
    assert active.loc[2, "ACT"] == pytest.approx(80 * expected_rate)
