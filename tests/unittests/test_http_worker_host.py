"""The HTTP worker can be bound to a specific host address."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from exit_codes import ExitCode

import cosmic_ray.cli
import cosmic_ray.distribution.http
from cosmic_ray.distribution.http import run_worker


@pytest.fixture
def captured_run_app(monkeypatch):
    """Record the arguments run_worker gives aiohttp instead of starting a server."""
    calls = []
    monkeypatch.setattr(cosmic_ray.distribution.http.web, "run_app", lambda app, **kwargs: calls.append(kwargs))
    return calls


def test_run_worker_binds_to_given_host(captured_run_app):
    run_worker(port=9876, host="127.0.0.1")

    assert captured_run_app == [{"host": "127.0.0.1", "port": 9876, "path": None}]


def test_run_worker_without_host_keeps_default_binding(captured_run_app):
    run_worker(port=9876)

    assert captured_run_app == [{"host": None, "port": 9876, "path": None}]


def test_run_worker_rejects_host_with_socket_path(captured_run_app, tmp_path):
    with pytest.raises(ValueError):
        run_worker(path=str(tmp_path / "worker.sock"), host="127.0.0.1")

    assert captured_run_app == []


@pytest.fixture
def captured_run_worker(monkeypatch):
    """Record the arguments the CLI gives run_worker instead of starting a server."""
    calls = []
    monkeypatch.setattr(cosmic_ray.distribution.http, "run_worker", lambda **kwargs: calls.append(kwargs))
    return calls


def test_cli_passes_host_to_worker(captured_run_worker):
    errcode = cosmic_ray.cli.main(["http-worker", "--port", "9876", "--host", "127.0.0.1"])

    assert errcode == ExitCode.OK
    assert captured_run_worker == [{"port": 9876, "path": None, "host": "127.0.0.1"}]


def test_cli_without_host_keeps_default_binding(captured_run_worker):
    errcode = cosmic_ray.cli.main(["http-worker", "--port", "9876"])

    assert errcode == ExitCode.OK
    assert captured_run_worker == [{"port": 9876, "path": None, "host": None}]


def test_cli_rejects_host_with_socket_path(captured_run_worker, tmp_path):
    errcode = cosmic_ray.cli.main(["http-worker", "--path", str(tmp_path / "worker.sock"), "--host", "127.0.0.1"])

    assert errcode == ExitCode.USAGE
    assert captured_run_worker == []


def _non_loopback_address():
    """Return an IPv4 address of this machine other than loopback, or None if there isn't one."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            # Connecting a UDP socket sends nothing; it only selects the outgoing interface.
            probe.connect(("192.0.2.1", 9))
            address = probe.getsockname()[0]
    except OSError:
        return None
    return None if address.startswith("127.") else address


def _can_connect(host, port):
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def test_worker_bound_to_loopback_is_unreachable_on_other_interfaces(tmp_path):
    """Start a real worker with --host 127.0.0.1 and check where it accepts connections."""
    other_address = _non_loopback_address()
    if other_address is None:
        pytest.skip("No non-loopback IPv4 address to check against")

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    source = Path(__file__).resolve().parents[2] / "src"
    env = dict(os.environ, PYTHONPATH=str(source))
    log_path = tmp_path / "worker.log"
    with log_path.open("w+") as log:
        worker = subprocess.Popen(
            [sys.executable, "-m", "cosmic_ray.cli", "http-worker", "--port", str(port), "--host", "127.0.0.1"],
            cwd=tmp_path,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 15
            while not _can_connect("127.0.0.1", port):
                assert worker.poll() is None, log_path.read_text()
                if time.monotonic() > deadline:
                    pytest.fail(f"Worker never listened on loopback: {log_path.read_text()}")
                time.sleep(0.02)

            assert not _can_connect(other_address, port)
        finally:
            worker.terminate()
            try:
                worker.wait(timeout=5)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait(timeout=5)
