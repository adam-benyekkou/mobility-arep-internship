import os

def test_install_r_packages_false_does_nothing(mod, monkeypatch):

    # If someone accidentally constructs RScript, make it obvious
    class ShouldNotBeCalled:
        def __init__(self, *a, **k):
            raise AssertionError("RScript should not be constructed when r_packages=False")
    monkeypatch.setattr(mod, "RScript", ShouldNotBeCalled)

    mod.install_r_packages(False)
    assert "R_LIBS" not in os.environ
