"""HTTP distribution must give workers each mutation's operator arguments."""

import asyncio
import os
import shlex
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

import cosmic_ray.distribution.http
from cosmic_ray.distribution.http import handle_mutate_and_test, send_request
from cosmic_ray.mutating import mutate_and_test
from cosmic_ray.work_item import MutationSpec, TestOutcome, WorkItem, WorkResult, WorkerOutcome


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


SUBJECT = "def f(x, z):\n    y = x + z\n    return y\n"

# VariableReplacer swaps ``x`` for a random constant in [-100, 100], so f(1000, 0) always exposes the mutant.
CATCHING_CHECK = "import subject\nassert subject.f(1000, 0) == 1000\n"
NON_CATCHING_CHECK = "import subject\n"


def _parameterised_mutation(module):
    return MutationSpec(module, "core/VariableReplacer", 0, (2, 4), (2, 13), operator_args={"cause_variable": "x"})


@pytest.mark.parametrize(
    "check, expected",
    [(CATCHING_CHECK, TestOutcome.KILLED), (NON_CATCHING_CHECK, TestOutcome.SURVIVED)],
    ids=["caught", "not-caught"],
)
def test_parameterised_operator_over_http_matches_local(native_http_worker, tmp_path, check, expected):
    """Without operator_args the worker errors, which is recorded as incompetent and counted as killed. That is only
    visibly wrong in the not-caught case, where the mutant should survive; the caught case checks the results match."""
    module = tmp_path / "subject.py"
    module.write_text(SUBJECT)
    script = tmp_path / "check.py"
    script.write_text(check)
    command = f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}"
    mutation = _parameterised_mutation(module)

    local = mutate_and_test([mutation], command, 5)
    remote = asyncio.run(send_request(native_http_worker, WorkItem.single("job", mutation), command, 5))

    assert local.worker_outcome == WorkerOutcome.NORMAL
    assert local.test_outcome == expected
    assert remote.worker_outcome == local.worker_outcome, remote.output
    assert remote.test_outcome == local.test_outcome, remote.output
    assert module.read_text() == SUBJECT


class _Request:
    """The part of an aiohttp request the handler reads."""

    def __init__(self, payload):
        self._payload = payload

    async def json(self):
        return self._payload


@pytest.fixture
def captured_mutations(monkeypatch):
    """Record the mutations the handler hands to mutate_and_test instead of running them."""
    calls = []

    def fake_mutate_and_test(mutations, test_command, timeout):
        calls.append(list(mutations))
        return WorkResult(worker_outcome=WorkerOutcome.NORMAL, output="", test_outcome=TestOutcome.SURVIVED, diff="")

    monkeypatch.setattr(cosmic_ray.distribution.http, "mutate_and_test", fake_mutate_and_test)
    return calls


def _payload(**mutation_fields):
    mutation = {"module_path": "subject.py", "operator": "core/VariableReplacer", "occurrence": 0, **mutation_fields}
    return {"mutations": [mutation], "test_command": "true", "timeout": 5}


def test_worker_passes_operator_args_to_mutation(captured_mutations):
    asyncio.run(handle_mutate_and_test(_Request(_payload(operator_args={"cause_variable": "x"}))))

    [[mutation]] = captured_mutations
    assert mutation.operator_args == {"cause_variable": "x"}


def test_worker_accepts_requests_without_operator_args(captured_mutations):
    """Coordinators from before operator_args was sent still work."""
    asyncio.run(handle_mutate_and_test(_Request(_payload())))

    [[mutation]] = captured_mutations
    assert mutation.operator_args == {}
