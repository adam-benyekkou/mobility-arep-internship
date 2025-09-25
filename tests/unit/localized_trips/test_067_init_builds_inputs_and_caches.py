from pathlib import Path
from mobility.localized_trips import LocalizedTrips

def test_init_builds_inputs_and_cache(
    project_dir,
    make_fake_trips_asset,
    patch_choice_models,
    fake_inputs_hash,
    localized_trips_base_filename,
):
    trips_asset = make_fake_trips_asset()
    localized_trips = LocalizedTrips(trips_asset)

    # Child models exist in inputs
    assert "travel_costs" in localized_trips.inputs
    assert "trans_mode_cm" in localized_trips.inputs
    assert "work_dest_cm" in localized_trips.inputs

    # Constructor arguments captured (transport_zones passed from population.inputs)
    assert patch_choice_models.travel_costs_constructor_args["transport_zones"].equals(
        trips_asset.inputs["population"].inputs["transport_zones"]
    )

    # Cache path rebased with hash prefix and correct filename
    expected_path = Path(project_dir) / f"{fake_inputs_hash}-{localized_trips_base_filename}"
    assert localized_trips.cache_path == expected_path
    assert localized_trips.hash_path.parent == project_dir
