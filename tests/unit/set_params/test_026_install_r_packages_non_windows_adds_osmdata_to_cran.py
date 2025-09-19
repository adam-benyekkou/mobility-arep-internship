from pathlib import Path
from types import SimpleNamespace
import sys

def test_install_r_packages_non_windows_adds_osmdata_to_cran(mod, monkeypatch, tmp_path):

    monkeypatch.setattr(mod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(sys, "executable", str(tmp_path / "bin" / "python"))

    def files_stub(pkg):
        return SimpleNamespace(joinpath=lambda p: tmp_path / pkg.replace(".", "_") / p)
    monkeypatch.setattr(mod.resources, "files", files_stub)

    seen = {"cran": None, "bin": None}
    class FakeRScript:
        def __init__(self, script_path): pass
        def run(self, args):
            # First call is CRAN, second is binaries; capture lists
            if seen["cran"] is None:
                seen["cran"] = list(args)
            else:
                seen["bin"] = list(args)
    monkeypatch.setattr(mod, "RScript", FakeRScript)

    mod.install_r_packages(True)

    assert "osmdata" in seen["cran"]          # on Linux, osmdata added to CRAN list
    assert seen["bin"] == []                  # no binaries on non-Windows
