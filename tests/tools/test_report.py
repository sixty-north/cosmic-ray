"Tests for cr-report."

import itertools
import subprocess
import sys

import pytest

SHOW_OUTPUT_OPTIONS = (None, "--show-output", "--no-show-output")
SHOW_DIFF_OPTIONS = (None, "--show-diff", "--no-show-diff")
SHOW_PENDING_OPTIONS = (None, "--show-pending", "--no-show-pending")
SURVIVING_ONLY_OPTIONS = (None, "--surviving-only", "--all-mutations")
OPTION_COMBINATIONS = (
    list(filter(None, combo))
    for combo in itertools.product(SHOW_OUTPUT_OPTIONS, SHOW_DIFF_OPTIONS, SHOW_PENDING_OPTIONS, SURVIVING_ONLY_OPTIONS)
)


@pytest.fixture(params=OPTION_COMBINATIONS)
def options(request):
    "All valid combinations of command line options for cr-report."
    return request.param


def test_smoke_test_for_report_on_initialized_session(initialized_session, options):
    command = [sys.executable, "-m", "cosmic_ray.tools.report"] + options + [str(initialized_session.session)]

    subprocess.check_call(command, cwd=str(initialized_session.session.parent))


def test_smoke_test_for_report_on_executed_session(execd_session):
    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.tools.report", str(execd_session.session)],
        cwd=str(execd_session.session.parent),
    )
