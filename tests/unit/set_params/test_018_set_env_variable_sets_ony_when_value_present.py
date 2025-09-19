import os

def test_set_env_variable_sets_only_when_value_present(mod, monkeypatch):

    # Clean slate
    monkeypatch.delenv("X_TEST", raising=False)

    mod.set_env_variable("X_TEST", "123")
    assert os.environ["X_TEST"] == "123"

    # None should not overwrite/remove
    mod.set_env_variable("X_TEST", None)
    assert os.environ["X_TEST"] == "123"
