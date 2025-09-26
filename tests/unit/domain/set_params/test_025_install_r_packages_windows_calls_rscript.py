import os
from pathlib import Path
from types import SimpleNamespace

def test_install_r_packages_windows_calls_rscript(mod, monkeypatch, tmp_path):
    import sys

    # Pretend we're on Windows
    monkeypatch.setattr(mod.platform, "system", lambda: "Windows")

    # Make sys.executable predictable
    fake_exe = tmp_path / "venv" / "python.exe"
    fake_exe.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(sys, "executable", str(fake_exe))

    # Stub resources.files so joinpath returns stable paths
    def files_stub(pkg):
        return SimpleNamespace(joinpath=lambda p: tmp_path / pkg.replace(".", "_") / p)
    monkeypatch.setattr(mod.resources, "files", files_stub)

    # Capture RScript calls
    calls = []
    class FakeRScript:
        def __init__(self, script_path):
            calls.append(("construct", str(script_path)))
        def run(self, args):
            calls.append(("run", list(args)))
    monkeypatch.setattr(mod, "RScript", FakeRScript)

    mod.install_r_packages(True)

    # R_LIBS points to <py_dir>/Lib/R/library
    expected_rlibs = Path(sys.executable).parent / "Lib" / "R" / "library"
    assert os.environ["R_LIBS"] == str(expected_rlibs)

    # We should see 2 script constructions and 2 runs
    constructs = [c for c in calls if c[0] == "construct"]
    runs = [c for c in calls if c[0] == "run"]
    assert len(constructs) == 2 and len(runs) == 2

    # The “binaries” list should contain the fake osmdata zip path on Windows
    binaries_args = runs[1][1]
    assert any(str(tmp_path) in s for s in binaries_args)
    assert any("mobility_resources" in s and s.endswith(".zip") for s in binaries_args)
