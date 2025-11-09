import pathlib
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from attrs import define


@pytest.fixture(scope="session")
def fast_tests_root(resources_dirpath):
    "Root directory for 'fast_tests'."
    return resources_dirpath / "fast_tests"


@define
class SessionData:
    config: Path
    session: Path


@pytest.fixture(scope="module")
def initialized_session(fast_tests_root):
    "Initialize a session in 'fast_tests_root' and return its path."
    config = fast_tests_root / "cr.conf"
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = pathlib.Path(tmp_path)
        session = tmp_path / "cr.db"
        subprocess.check_call(
            [sys.executable, "-m", "cosmic_ray.cli", "init", str(config), str(session)], cwd=str(fast_tests_root)
        )
        yield SessionData(config, session)


@pytest.fixture(scope="module")
def execd_session(fast_tests_root):
    "Initialize and exec a session in 'fast_test_root' and return its path."
    config = fast_tests_root / "cr.conf"
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = pathlib.Path(tmp_path)
        session = tmp_path / "cr.db"

        subprocess.check_call(
            [sys.executable, "-m", "cosmic_ray.cli", "init", str(config), str(session)], cwd=str(fast_tests_root)
        )

        subprocess.check_call(
            [sys.executable, "-m", "cosmic_ray.cli", "exec", str(config), str(session)], cwd=str(fast_tests_root)
        )

        yield SessionData(config, session)
