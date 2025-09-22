import pytest

def test_init_invalid_mode_raises(fake_transport_zones):
    import mobility.travel_costs as mod
    with pytest.raises(ValueError):
        mod.TravelCosts(fake_transport_zones, "rocket")
