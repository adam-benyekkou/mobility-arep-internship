def test_init_builds_inputs_and_cache(monkeypatch, project_dir, fake_transport_zones_asset, fake_travel_costs_asset):
    import mobility.destination_choice_model as mod

    # Avoid JSON-serialization and auto-get in Asset.__init__
    monkeypatch.setattr(mod.Asset, "compute_inputs_hash", lambda self: "deadbeef")
    monkeypatch.setattr(mod.Asset, "get", lambda self: None)

    class DummyDCM(mod.DestinationChoiceModel):
        def prepare_sources_and_sinks(self, *a, **k):
            return None, None

    model = DummyDCM(
        motive="work",
        transport_zones=fake_transport_zones_asset,
        travel_costs=fake_travel_costs_asset,
        cost_of_time=30.0,
    )

    assert model.cache_path.parent == project_dir
    # hash prefix is kept; we just check suffix
    assert str(model.cache_path.name).endswith("work_destination_choice_model.parquet")
    assert model.inputs["motive"] == "work"
    assert model.inputs["travel_costs"] is fake_travel_costs_asset
    assert model.inputs["cost_of_time"] == 30.0
