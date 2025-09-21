import os
import subprocess
import sys

import pytest

# Skip these tests when running in GitHub Actions where a proper git
# workspace isn't available in the test environment.
skip_in_ci = pytest.mark.xfail(
    os.environ.get("GITHUB_ACTIONS") == "true",
    reason="This test failes on non-master branches in CI, so we ignore this problem for now.",
)


@skip_in_ci
def test_smoke_test_on_initialized_session(initialized_session, fast_tests_root):
    command = [sys.executable, "-m", "cosmic_ray.tools.filters.git", str(initialized_session.session)]

    subprocess.check_call(command, cwd=str(fast_tests_root))


@skip_in_ci
def test_smoke_test_on_execd_session(execd_session, fast_tests_root):
    command = [sys.executable, "-m", "cosmic_ray.tools.filters.git", str(execd_session.session)]

    subprocess.check_call(command, cwd=str(fast_tests_root))
