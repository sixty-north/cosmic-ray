import os
import pathlib
import subprocess
import sys

import pytest

from cosmic_ray.tools.survival_rate import survival_rate
from cosmic_ray.work_db import WorkDB, use_db


@pytest.fixture(scope="session")
def example_project_root(pytestconfig):
    root = pathlib.Path(str(pytestconfig.rootdir))
    return root / "resources" / "example_project"


@pytest.fixture
def config(tester, distributor):
    "Get config file name."
    config = f"cosmic-ray.{tester}.{distributor}.conf"
    return config


@pytest.mark.slow
def test_init_and_exec(example_project_root, config, session):
    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "init", config, str(session)], cwd=str(example_project_root)
    )

    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "exec", config, str(session)], cwd=str(example_project_root)
    )

    session_path = example_project_root / session
    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        rate = survival_rate(work_db)
        assert rate == 0.0


def test_baseline_with_explicit_session_file(example_project_root, config, session):
    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "baseline", str(config), "--session-file", str(session)],
        cwd=str(example_project_root),
    )

    with use_db(str(session), WorkDB.Mode.open) as work_db:
        rate = survival_rate(work_db)
        assert rate == 100.0


def test_baseline_with_temp_session_file(example_project_root, config):
    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "baseline", str(config)],
        cwd=str(example_project_root),
    )


def test_importing(example_project_root, session):
    config = "cosmic-ray.import.conf"

    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "init", config, str(session)],
        cwd=str(example_project_root),
    )

    session_path = example_project_root / session
    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        rate = survival_rate(work_db)
        assert rate == 0.0


def test_empty___init__(example_project_root, session):
    config = "cosmic-ray.empty.conf"

    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "init", str(config), str(session)],
        cwd=str(example_project_root),
    )

    session_path = example_project_root / session
    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        rate = survival_rate(work_db)
        assert rate == 0.0


def test_inexisting(example_project_root, session):
    config = "cosmic-ray.inexisting.conf"

    result = subprocess.run(
        [sys.executable, "-m", "cosmic_ray.cli", "init", str(config), str(session)],
        cwd=str(example_project_root),
        encoding="utf-8",
        capture_output=True,
    )

    assert result.returncode == 66
    assert result.stdout == ""
    assert result.stderr == "Could not find module path example/unknown_file.py" + os.linesep


def test_baseline_with_pytest_filter(example_project_root, session):
    config = "cosmic-ray.with-pytest-filter.conf"

    result = subprocess.run(
        [sys.executable, "-m", "cosmic_ray.cli", "baseline", str(config)],
        cwd=str(example_project_root),
        encoding="utf-8",
        capture_output=True,
    )

    assert result.returncode == 0
