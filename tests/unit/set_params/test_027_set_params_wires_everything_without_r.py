import os
from pathlib import Path
import sys

def test_set_params_wires_everything_without_r(mod, monkeypatch, tmp_path):
    # Start from a clean env so old values don't mask failures
    for key in [
        "MOBILITY_ENV_PATH",
        "MOBILITY_CERT_FILE",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "MOBILITY_PACKAGE_DATA_FOLDER",
        "MOBILITY_PROJECT_DATA_FOLDER",
        "R_LIBS",
    ]:
        monkeypatch.delenv(key, raising=False)

    # Make sys.executable predictable -> MOBILITY_ENV_PATH derives from this
    fake_exe = tmp_path / "venv" / "python.exe"
    fake_exe.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(sys, "executable", str(fake_exe))

    # Provide custom paths; ensure they exist so os.makedirs won't be needed
    pkg_dir = tmp_path / "pkg"
    proj_dir = tmp_path / "proj"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    proj_dir.mkdir(parents=True, exist_ok=True)

    # Guard: RScript must not be invoked when r_packages=False
    class ShouldNotBeCalled:
        def __init__(self, *a, **k):
            raise AssertionError("RScript must not be created")
    monkeypatch.setattr(mod, "RScript", ShouldNotBeCalled)

    assert "R_LIBS" not in os.environ  # precondition

    mod.set_params(
        package_data_folder_path=str(pkg_dir),
        project_data_folder_path=str(proj_dir),
        path_to_pem_file="C:/certs/cert.pem",
        http_proxy_url="http://proxy",
        https_proxy_url="https://proxy",
        r_packages=False,
    )

    # Env vars should be set as expected
    assert os.environ["MOBILITY_ENV_PATH"] == str(Path(sys.executable).parent)
    assert os.environ["MOBILITY_CERT_FILE"] == "C:/certs/cert.pem"
    assert os.environ["HTTP_PROXY"] == "http://proxy"
    assert os.environ["HTTPS_PROXY"] == "https://proxy"
    assert os.environ["MOBILITY_PACKAGE_DATA_FOLDER"] == str(pkg_dir)
    assert os.environ["MOBILITY_PROJECT_DATA_FOLDER"] == str(proj_dir)
    assert "R_LIBS" not in os.environ  # still absent when r_packages=False
