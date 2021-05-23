import pathlib
import subprocess
import tempfile
import sys

import pytest


@pytest.fixture(scope="session")
def fast_tests_root(pytestconfig):
    "Root directory for 'fast_tests'."
    root = pathlib.Path(str(pytestconfig.rootdir))
    return root / "resources" / "fast_tests"


@pytest.fixture(scope="module")
def initialized_session(fast_tests_root):
    "Initialize a session in 'fast_tests_root' and return its path."
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = pathlib.Path(tmp_path)
        session = tmp_path / "cr.db"
        subprocess.check_call(
            [sys.executable, "-m", "cosmic_ray.cli", "init", "cr.conf", str(session)], cwd=str(fast_tests_root)
        )
        yield session


@pytest.fixture(scope="module")
def execd_session(fast_tests_root):
    "Initialize and exec a session in 'fast_test_root' and return its path."
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = pathlib.Path(tmp_path)
        session = tmp_path / "cr.db"

        subprocess.check_call(
            [sys.executable, "-m", "cosmic_ray.cli", "init", "cr.conf", str(session)], cwd=str(fast_tests_root)
        )

        subprocess.check_call(
            [sys.executable, "-m", "cosmic_ray.cli", "exec", "cr.conf", str(session)], cwd=str(fast_tests_root)
        )

        yield session
