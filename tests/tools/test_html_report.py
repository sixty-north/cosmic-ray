import itertools
import subprocess
import sys

import pytest

ONLY_COMPLETED_OPTIONS = (None, "--only-completed", "--not-only-completed")
SKIP_SUCCESS_OPTIONS = (None, "--skip-success", "--include-success")
OPTION_COMBINATIONS = (
    list(filter(None, combo)) for combo in itertools.product(ONLY_COMPLETED_OPTIONS, SKIP_SUCCESS_OPTIONS)
)


@pytest.fixture(params=OPTION_COMBINATIONS)
def options(request):
    "All valid combinations of command line options for cr-report."
    return request.param


def test_smoke_test_on_initialized_session(initialized_session, options):
    command = [sys.executable, "-m", "cosmic_ray.tools.html"] + options + [str(initialized_session.session)]

    subprocess.check_call(command, cwd=str(initialized_session.session.parent))


def test_smoke_test_on_execd_session(execd_session, options):
    command = [sys.executable, "-m", "cosmic_ray.tools.html"] + options + [str(execd_session.session)]

    subprocess.check_call(command, cwd=str(execd_session.session.parent))
