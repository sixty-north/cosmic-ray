"""HTTP transport must preserve native mutation and trial-timeout semantics."""

import asyncio
import math
import os
import shlex
import socket
import subprocess
import sys
import time
from pathlib import Path

import aiohttp
import pytest

from cosmic_ray.distribution.http import send_request
from cosmic_ray.work_item import TestOutcome, WorkItem, WorkerOutcome


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


@pytest.mark.parametrize("trial_timeout", [1, 900])
def test_http_deadline_outlasts_trial_budget(native_http_worker, tmp_path, monkeypatch, trial_timeout):
    script = tmp_path / "slow_check.py"
    script.write_text("import time\ntime.sleep(0.1)\nprint('native trial completed')\n")
    # Compress aiohttp's unrelated 300-second default to avoid a five-minute
    # regression test. A supplied transport policy must override this default.
    monkeypatch.setattr(aiohttp.client, "DEFAULT_TIMEOUT", aiohttp.ClientTimeout(total=0.01))
    requests = []
    real_request = aiohttp.request

    def record_request(*args, **kwargs):
        requests.append(kwargs)
        return real_request(*args, **kwargs)

    monkeypatch.setattr(aiohttp, "request", record_request)
    result = asyncio.run(send_request(native_http_worker, WorkItem("slow-trial", ()), _command(script), trial_timeout))

    assert result.worker_outcome == WorkerOutcome.NORMAL
    assert result.test_outcome == TestOutcome.SURVIVED
    assert "native trial completed" in result.output
    policy = requests[0]["timeout"]
    assert isinstance(policy, aiohttp.ClientTimeout)
    assert policy.total is not None and math.isfinite(policy.total)
    assert policy.total > trial_timeout
    assert policy.connect is not None and math.isfinite(policy.connect)
    assert 0 < policy.connect <= policy.total
    assert requests[0]["json"]["timeout"] == trial_timeout


def test_native_trial_timeout_still_returns_worker_result(native_http_worker, tmp_path):
    script = tmp_path / "hung_check.py"
    script.write_text("import time\ntime.sleep(10)\n")

    result = asyncio.run(send_request(native_http_worker, WorkItem("hung-trial", ()), _command(script), 0.1))

    assert result.worker_outcome == WorkerOutcome.NORMAL
    assert result.test_outcome == TestOutcome.KILLED
    assert result.output == "timeout"
