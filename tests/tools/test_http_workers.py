"""The installed launcher starts native workers from isolated local Git clones."""

import asyncio
import os
import shlex
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from cosmic_ray.distribution.http import send_request
from cosmic_ray.work_item import MutationSpec, TestOutcome, WorkItem, WorkerOutcome


@pytest.mark.skipif(os.name != "posix", reason="Bounded launcher cleanup uses POSIX process groups")
def test_launcher_processes_native_mutation_without_ambient_event_loop(tmp_path):
    """Exercise cr-http-workers itself, including its child cosmic-ray command."""
    repo = tmp_path / "local-repository"
    repo.mkdir()
    original = "value = 1\n"
    (repo / "subject.py").write_text(original)
    (repo / "check.py").write_text(
        "from pathlib import Path\n"
        "import os\n"
        "import subject\n"
        "print(f'worker pid: {os.getppid()}', flush=True)\n"
        "print(f'worker cwd: {Path.cwd()}', flush=True)\n"
        "print(f'observed value: {subject.value}', flush=True)\n"
        "assert subject.value == 1\n"
    )
    git_env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    for args in (
        ["init", "--quiet"],
        ["add", "subject.py", "check.py"],
        ["-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--quiet", "-m", "fixture"],
    ):
        subprocess.run(["git", *args], cwd=repo, env=git_env, capture_output=True, check=True, timeout=10)

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    config = tmp_path / "cosmic-ray.toml"
    config.write_text(f'[cosmic-ray.distributor.http]\nworker-urls = ["{url}"]\n')
    scripts = Path(sys.executable).parent
    launcher = scripts / "cr-http-workers"
    assert launcher.is_file(), "Install this checkout in the test interpreter's environment"
    source = Path(__file__).resolve().parents[2] / "src"
    env = dict(git_env, PYTHONPATH=str(source), PATH=f"{scripts}{os.pathsep}{os.environ.get('PATH', '')}")
    log_path = tmp_path / "launcher.log"
    with log_path.open("w+") as log:
        process = subprocess.Popen(
            [str(launcher), str(config), str(repo)],
            cwd=tmp_path,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            deadline = time.monotonic() + 15
            while True:
                assert process.poll() is None, f"cr-http-workers exited before worker startup:\n{log_path.read_text()}"
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    if time.monotonic() > deadline:
                        pytest.fail(f"Launched worker never listened:\n{log_path.read_text()}")
                    time.sleep(0.02)

            mutation = MutationSpec(Path("subject.py"), "core/NumberReplacer", 0, (1, 8), (1, 9))
            result = asyncio.run(
                asyncio.wait_for(
                    send_request(
                        url, WorkItem.single("launcher-trial", mutation), f"{shlex.quote(sys.executable)} check.py", 5
                    ),
                    timeout=10,
                )
            )

            assert result.worker_outcome == WorkerOutcome.NORMAL
            assert result.test_outcome == TestOutcome.KILLED
            assert "observed value: 2" in result.output
            assert result.diff
            clone_lines = [line for line in result.output.splitlines() if line.startswith("worker cwd: ")]
            assert len(clone_lines) == 1
            clone = Path(clone_lines[0].removeprefix("worker cwd: "))
            assert clone.resolve() != repo.resolve()
            assert (clone / ".git").is_dir()
            assert (clone / "subject.py").read_text() == original
            assert (repo / "subject.py").read_text() == original

            pid_lines = [line for line in result.output.splitlines() if line.startswith("worker pid: ")]
            assert len(pid_lines) == 1
            worker_pid = int(pid_lines[0].removeprefix("worker pid: "))
            assert os.getpgid(worker_pid) == process.pid
            os.kill(worker_pid, signal.SIGTERM)
            assert process.wait(timeout=10) == 0, log_path.read_text()
            assert not clone.exists()
        finally:
            # The launcher owns shell grandchildren: stopping only its parent
            # PID would leak workers. Signal the isolated process group instead.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
