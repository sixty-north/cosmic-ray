import os
import subprocess
import sys
from pathlib import Path

import pytest

from cosmic_ray.tools.filters.git import GitFilter

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


def test_git_news_ignores_binary_data_in_diff(monkeypatch):
    diff_output = b"\n".join(
        [
            b"diff --git a/tests/resources/blob.bin b/tests/resources/blob.bin",
            b"new file mode 100644",
            b"index 0000000..1111111",
            b"Binary files /dev/null and b/tests/resources/blob.bin differ \x92",
            b"diff --git a/src/example.py b/src/example.py",
            b"index 1234567..89abcde 100644",
            b"--- a/src/example.py",
            b"+++ b/src/example.py",
            b"@@ -0,0 +1,2 @@",
            b"+print('hello')",
            b"+print('world')",
        ]
    )

    def fake_check_output(command, stderr):
        return diff_output

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    assert GitFilter()._git_news("master") == {Path("src/example.py"): {1, 2}}
