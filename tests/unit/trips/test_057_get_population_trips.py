# tests/unit/trips/test_057_get_population_trips.py
import pandas as pd

def test_get_population_trips(monkeypatch, fake_population, patch_mobility_survey):
    import mobility.trips as mod

    trips = mod.Trips(fake_population)

    def fake_get_individual_trips(self, csp, csp_household, urban_unit_category, n_pers, n_cars, n_years=1):
        # two trips per person
        return pd.DataFrame(
            {
                "trip_id": ["seed1", "seed2"],  # will be overwritten by uuid-* in get_population_trips
                "previous_motive": ["pm1", "pm2"],
                "motive": ["M1", "M2"],
                "mode_id": [1, 2],
                "distance": [1.0, 2.0],
                "n_other_passengers": [0, 1],
                "trip_type": ["short", "long"],
            }
        )

    monkeypatch.setattr(mod.Trips, "get_individual_trips", fake_get_individual_trips, raising=True)

    tz_df = fake_population.inputs["transport_zones"].get()
    pop_df = fake_population.get()

    out = trips.get_population_trips(pop_df, tz_df)

    # two individuals x two trips each = 4 rows
    assert len(out) == 4

    # trip_id overwritten with deterministic uuid-*
    assert out["trip_id"].str.startswith("uuid-").all()
    assert out["trip_id"].nunique() == 4

    # individual ids assigned
    assert set(out["individual_id"]) == {"p1", "p2"}

    # required columns present
    for col in ["previous_motive", "motive", "mode_id", "distance", "n_other_passengers", "trip_type"]:
        assert col in out.columns
