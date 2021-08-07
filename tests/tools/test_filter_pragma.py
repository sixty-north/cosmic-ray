import subprocess
import sys


def test_smoke_test_on_initialized_session(initialized_session, fast_tests_root):
    command = [sys.executable, "-m", "cosmic_ray.tools.filters.pragma_no_mutate", str(initialized_session.session)]

    subprocess.check_call(command, cwd=str(fast_tests_root))


def test_smoke_test_on_execd_session(execd_session, fast_tests_root):
    command = [sys.executable, "-m", "cosmic_ray.tools.filters.pragma_no_mutate", str(execd_session.session)]

    subprocess.check_call(command, cwd=str(fast_tests_root))
