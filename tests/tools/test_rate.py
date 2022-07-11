import subprocess
import sys


def test_smoke_test_for_initialized_session(initialized_session):
    command = [sys.executable, "-m", "cosmic_ray.tools.survival_rate", str(initialized_session.session)]

    proc = subprocess.run(command, cwd=str(initialized_session.session.parent), capture_output=True)
    assert proc.returncode == 0
    assert float(proc.stdout) == 0


def test_smoke_test_for_execd_session(execd_session):
    command = [sys.executable, "-m", "cosmic_ray.tools.survival_rate", str(execd_session.session)]

    proc = subprocess.run(command, cwd=str(execd_session.session.parent), capture_output=True)
    assert proc.returncode == 0
    assert float(proc.stdout) == 18.18
