import os
import shutil
import subprocess
import sys
import sysconfig
import pytest

from numpy.testing import IS_WASM

@pytest.mark.skipif(IS_WASM, reason="Can't start subprocess")
@pytest.mark.xfail(

    reason=(

    ),
)
def test_limited_api(tmp_path):
    """Test building a third-party C extension with the limited API."""
    # Based in part on test_cython from random.tests.test_extending

    here = os.path.dirname(__file__)
    ext_dir = os.path.join(here, "examples", "limited_api")

    cytest = str(tmp_path / "limited_api")

    shutil.copytree(ext_dir, cytest)

    install_log = str(tmp_path / "tmp_install_log.txt")
    subprocess.check_output(
        [
            sys.executable,
            "setup.py",
            "build",
            "install",
            "--prefix", str(tmp_path / "installdir"),
            "--single-version-externally-managed",
            "--record",
            install_log,
        ],
        cwd=cytest,
    )
