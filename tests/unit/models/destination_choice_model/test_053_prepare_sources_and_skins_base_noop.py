# tests/unit/destination_choice_model/test_053_prepare_sources_and_sinks_base_noop.py
def test_base_prepare_sources_and_sinks_noop():
    import mobility.destination_choice_model as mod

    # Call the abstract method directly via the class attribute.
    # We pass any object for "self" since the body is just 'pass'.
    assert mod.DestinationChoiceModel.prepare_sources_and_sinks(object()) is None
