import subprocess
import sys


def test_smoke_test_for_initialized_session(initialized_session):
    command = [sys.executable, "-m", "cosmic_ray.tools.survival_rate", str(initialized_session)]

    subprocess.check_call(command, cwd=str(initialized_session.parent))


def test_smoke_test_for_execd_session(execd_session):
    command = [sys.executable, "-m", "cosmic_ray.tools.survival_rate", str(execd_session)]

    subprocess.check_call(command, cwd=str(execd_session.parent))
