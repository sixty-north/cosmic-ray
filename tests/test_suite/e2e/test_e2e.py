import pathlib
import subprocess
import sys

import pytest

from cosmic_ray.work_db import use_db, WorkDB
from cosmic_ray.tools.survival_rate import survival_rate


@pytest.fixture(scope="session")
def example_project_root():
    root = pathlib.Path(str(pytest.config.rootdir))
    return root / ".." / "example_project"


@pytest.fixture
def config(tester, engine):
    "Get config file name."
    config = "cosmic-ray.{}.{}.conf".format(tester, engine)
    return config


def test_e2e(example_project_root, config, session):
    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "init", config,
         str(session)],
        cwd=str(example_project_root))

    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "exec",
         str(session)],
        cwd=str(example_project_root))

    session_path = example_project_root / session
    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        rate = survival_rate(work_db)
        assert rate == 0.0


def test_importing(example_project_root, session):
    config = "cosmic-ray.import.conf"

    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "init", config,
         str(session)],
        cwd=str(example_project_root),
    )

    session_path = example_project_root / session
    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        rate = survival_rate(work_db)
        assert rate == 0.0


def test_empty___init__(example_project_root, session):
    config = "cosmic-ray.empty.conf"

    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "init", config,
         str(session)],
        cwd=str(example_project_root),
    )

    session_path = example_project_root / session
    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        rate = survival_rate(work_db)
        assert rate == 0.0


def test_failing_baseline(example_project_root, session):
    config = "cosmic-ray.baseline_fail.conf"

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(
            [
                sys.executable, "-m", "cosmic_ray.cli", "init", config,
                str(session)
            ],
            cwd=str(example_project_root),
        )


def test_config_command(example_project_root, session):
    config = "cosmic-ray.import.conf"

    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "init", config,
         str(session)],
        cwd=str(example_project_root),
    )

    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "config",
         str(session)],
        cwd=str(example_project_root),
    )
