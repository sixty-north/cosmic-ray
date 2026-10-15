"""HTTP distribution owns its event loop when called synchronously."""

import asyncio
import os
import shlex
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from cosmic_ray.distribution.http import HttpDistributor
from cosmic_ray.work_item import MutationSpec, TestOutcome, WorkItem, WorkerOutcome


@pytest.fixture
def native_http_worker(tmp_path):
    """Serve the unchanged native endpoint in an isolated Python process."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    source = Path(__file__).resolve().parents[2] / "src"
    env = dict(os.environ, PYTHONPATH=str(source))
    log_path = tmp_path / "worker.log"
    with log_path.open("w+") as log:
        worker = subprocess.Popen(
            [sys.executable, "-c", f"from cosmic_ray.distribution.http import run_worker; run_worker(port={port})"],
            cwd=tmp_path,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 15
            while True:
                assert worker.poll() is None, log_path.read_text()
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    if time.monotonic() > deadline:
                        pytest.fail(f"Native HTTP worker never listened: {log_path.read_text()}")
                    time.sleep(0.02)
            yield f"http://127.0.0.1:{port}"
        finally:
            worker.terminate()
            try:
                worker.wait(timeout=5)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait(timeout=5)


def _command(script):
    return f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}"


def test_sync_distributor_runs_native_mutation_without_ambient_event_loop(native_http_worker, tmp_path):
    module = tmp_path / "subject.py"
    original = "value = 1\n"
    module.write_text(original)
    script = tmp_path / "check.py"
    script.write_text(
        "import subject\nprint(f'observed value: {subject.value}', flush=True)\nassert subject.value == 1\n"
    )
    mutation = MutationSpec(module, "core/NumberReplacer", 0, (1, 8), (1, 9))
    completed = []
    # Python 3.14 no longer implicitly creates this loop. Exercise the public
    # synchronous controller, not _process() behind a test-owned event loop.
    asyncio.set_event_loop(None)

    HttpDistributor()(
        [WorkItem.single("actual-mutation", mutation)],
        _command(script),
        5,
        {"worker-urls": [native_http_worker]},
        lambda job_id, result: completed.append((job_id, result)),
    )

    assert len(completed) == 1
    job_id, result = completed[0]
    assert job_id == "actual-mutation"
    assert result.worker_outcome == WorkerOutcome.NORMAL
    assert result.test_outcome == TestOutcome.KILLED
    assert "observed value: 2" in result.output
    assert result.diff
    assert module.read_text() == original
