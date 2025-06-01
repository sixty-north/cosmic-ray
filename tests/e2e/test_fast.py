import pathlib
import subprocess
import sys

import pytest

from cosmic_ray.tools.survival_rate import survival_rate
from cosmic_ray.work_db import WorkDB, use_db


@pytest.fixture(scope="session")
def project_root(pytestconfig):
    root = pathlib.Path(str(pytestconfig.rootdir))
    return root / "tests" / "resources" / "fast_tests"


def test_fast_tests(project_root, session):
    """This tests that CR works correctly on suites that execute very rapidly.

    A single mutation-test round can be faster than the resolution of file timestamps for some filesystems. When this
    happens, we found that Python would not correctly create new pyc files - because it had no way to know do do so! We
    modified CR to work around this problem, and this test tries to ensure that we don't regress.
    """
    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "init", "cr.conf", str(session)], cwd=str(project_root)
    )

    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "exec", "cr.conf", str(session)], cwd=str(project_root)
    )

    session_path = project_root / session
    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        rate = survival_rate(work_db)
        assert round(rate, 2) == 18.18
