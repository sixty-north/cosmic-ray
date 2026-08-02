"Tests for cosmic_ray.testing."

import sys
import time

from cosmic_ray.testing import run_tests
from cosmic_ray.work_item import TestOutcome


def test_run_tests_survived_on_success():
    outcome, _ = run_tests(f'{sys.executable} -c "pass"', 30)
    assert outcome == TestOutcome.SURVIVED


def test_run_tests_killed_on_failure():
    outcome, _ = run_tests(f'{sys.executable} -c "raise SystemExit(1)"', 30)
    assert outcome == TestOutcome.KILLED


def test_run_tests_timeout_kills_spawned_descendants(tmp_path):
    """A timed-out test command must not leave orphaned grandchildren running."""
    marker = tmp_path / "marker"
    grandchild = tmp_path / "grandchild.py"
    grandchild.write_text(f"import time, pathlib\ntime.sleep(5)\npathlib.Path({str(marker)!r}).write_text('alive')\n")
    child = tmp_path / "child.py"
    child.write_text(
        f"import subprocess, sys, time\nsubprocess.Popen([sys.executable, {str(grandchild)!r}])\ntime.sleep(30)\n"
    )

    outcome, _ = run_tests(f"{sys.executable} {child}", 1)
    assert outcome == TestOutcome.KILLED

    # Give the grandchild more than its sleep to write the marker if it survived.
    time.sleep(7)
    assert not marker.exists()
