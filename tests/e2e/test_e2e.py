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
    return root / "tests" / "resources" / "example_project"


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

    # Workaround to take out new line in result.stderr value that causes error in Windows,
    # despite using os.linesep
    stripped_version = result.stderr.strip()

    assert result.returncode == 66
    assert result.stdout == ""
    assert stripped_version == "Could not find module path example" + os.sep + "unknown_file.py"


def test_baseline_with_pytest_filter(example_project_root, session):
    config = "cosmic-ray.with-pytest-filter.conf"

    result = subprocess.run(
        [sys.executable, "-m", "cosmic_ray.cli", "baseline", str(config)],
        cwd=str(example_project_root),
        encoding="utf-8",
        capture_output=True,
    )

    assert result.returncode == 0


@pytest.mark.slow
def test_reinit_session_with_results_fails(example_project_root, config, session):
    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "init", config, str(session)], cwd=str(example_project_root)
    )

    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "exec", config, str(session)], cwd=str(example_project_root)
    )

    session_path = example_project_root / session
    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        initial_num_work_items = work_db.num_work_items
        assert work_db.num_results == initial_num_work_items > 0

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(
            [sys.executable, "-m", "cosmic_ray.cli", "init", config, str(session)], cwd=str(example_project_root)
        )

    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        assert work_db.num_results == work_db.num_work_items == initial_num_work_items


@pytest.mark.slow
def test_force_reinit_session_with_results_succeeds(example_project_root, config, session):
    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "init", config, str(session)], cwd=str(example_project_root)
    )

    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "exec", config, str(session)], cwd=str(example_project_root)
    )

    session_path = example_project_root / session
    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        initial_num_work_items = work_db.num_work_items
        assert initial_num_work_items > 0
        assert work_db.num_results == work_db.num_work_items

    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "init", config, str(session), "--force"], cwd=str(example_project_root)
    )

    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        assert work_db.num_work_items == initial_num_work_items
        assert work_db.num_results == 0
