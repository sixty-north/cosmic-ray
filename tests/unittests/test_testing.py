"Tests for cosmic_ray.testing."

import shlex
import sys
import time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import cosmic_ray.testing as testing
from cosmic_ray.config import ConfigValueError
from cosmic_ray.testing import run_tests
from cosmic_ray.work_item import TestOutcome

PYTHON = shlex.quote(sys.executable)


def test_run_tests_survived_on_success():
    outcome, _ = run_tests(f'{PYTHON} -c "pass"', 30)
    assert outcome == TestOutcome.SURVIVED


def test_run_tests_killed_on_failure():
    outcome, _ = run_tests(f'{PYTHON} -c "raise SystemExit(1)"', 30)
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

    outcome, _ = run_tests(f"{PYTHON} {shlex.quote(str(child))}", 1)
    assert outcome == TestOutcome.KILLED

    # Give the grandchild more than its sleep to write the marker if it survived.
    time.sleep(7)
    assert not marker.exists()


@pytest.mark.skipif(sys.platform not in ("linux", "win32"), reason="Memory limits require Linux or Windows")
def test_run_tests_memory_limit_kills_a_runaway_test():
    """A test command that allocates past the limit fails fast instead of exhausting memory."""
    hog = f'{PYTHON} -c "import time; block = bytearray(600 * 2**20); time.sleep(30)"'
    started = time.monotonic()
    outcome, _ = run_tests(hog, 60, memory_limit_mb=200)
    assert outcome == TestOutcome.KILLED
    assert time.monotonic() - started < 20


@pytest.mark.skipif(sys.platform not in ("linux", "win32"), reason="Memory limits require Linux or Windows")
def test_run_tests_memory_limit_leaves_a_small_test_alone():
    outcome, _ = run_tests(f'{PYTHON} -c "block = bytearray(10 * 2**20)"', 30, memory_limit_mb=200)
    assert outcome == TestOutcome.SURVIVED


@pytest.mark.parametrize("platform", ["darwin", "freebsd14"])
def test_unsupported_memory_limit_never_launches_a_process(monkeypatch, platform):
    monkeypatch.setattr(testing, "sys", SimpleNamespace(platform=platform))
    launch = Mock()
    monkeypatch.setattr(testing.subprocess, "Popen", launch)
    with pytest.raises(ConfigValueError, match="supported only on Linux and Windows"):
        run_tests("unused", 5, memory_limit_mb=200)
    launch.assert_not_called()


@pytest.mark.parametrize("stage", ["assignment", "resumption"])
def test_windows_adoption_failure_cleans_up_child(monkeypatch, stage):
    monkeypatch.setattr(testing, "sys", SimpleNamespace(platform="win32"))
    job = Mock()
    job.adopt.side_effect = OSError(f"{stage} failed")
    monkeypatch.setattr(testing, "Job", Mock(return_value=job), raising=False)
    monkeypatch.setattr(testing, "CREATE_SUSPENDED", 4, raising=False)
    proc = Mock()
    monkeypatch.setattr(testing.subprocess, "Popen", Mock(return_value=proc))

    outcome, output = run_tests("unused", 5)

    assert outcome == TestOutcome.INCOMPETENT
    assert f"{stage} failed" in output
    proc.kill.assert_called_once_with()
    proc.wait.assert_called_once_with()
    proc.stdout.close.assert_called_once_with()
    proc.stderr.close.assert_called_once_with()
    proc.communicate.assert_not_called()
    job.close.assert_called_once_with()
