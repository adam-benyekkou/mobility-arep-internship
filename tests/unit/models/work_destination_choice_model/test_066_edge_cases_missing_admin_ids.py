import pandas as pd
import pytest

def test_missing_admin_ids_raises_keyerror(fake_transport_zones):
    """
    If transport_zones references an admin_id not present in the inputs,
    .loc[...] should raise a KeyError (current behavior).
    This documents the contract; if you later choose to change behavior
    (e.g., use intersection), update the test accordingly.
    """
    import mobility.work_destination_choice_model as mod

    # active only covers A1 and A3; A2 is missing -> expect KeyError
    idx = pd.Index(["A1", "A3"], name="CODGEO")
    active = pd.DataFrame({"men": [1, 3], "women": [4, 5]}, index=idx)

    dummy_costs = pd.DataFrame()
    m = mod.WorkDestinationChoiceModel(fake_transport_zones, dummy_costs)

    with pytest.raises(KeyError):
        _ = m.prepare_sources(fake_transport_zones, active)
