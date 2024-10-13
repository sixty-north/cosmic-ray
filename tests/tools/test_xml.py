import subprocess
import sys


def test_smoke_test_initialized_session(initialized_session):
    command = [sys.executable, "-m", "cosmic_ray.tools.xml", str(initialized_session.session)]

    subprocess.check_call(command, cwd=str(initialized_session.session.parent))


def test_smoke_test_execd_session(execd_session):
    command = [sys.executable, "-m", "cosmic_ray.tools.xml", str(execd_session.session)]

    subprocess.check_call(command, cwd=str(execd_session.session.parent))
