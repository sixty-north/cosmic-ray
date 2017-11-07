import pathlib
import subprocess

import pytest

from cosmic_ray.work_db import use_db, WorkDB
from cosmic_ray.reporting import survival_rate


TEST_RUNNERS = ('unittest', 'pytest', 'nosetest')
ENGINES = ('local',)  # TODO: Add celery3


@pytest.fixture(params=TEST_RUNNERS)
def test_runner(request):
    return request.param


@pytest.fixture(params=ENGINES)
def engine(request):
    return request.param


@pytest.fixture
def project_root():
    root = pathlib.Path(str(pytest.config.rootdir))
    return root / 'test_project'


def test_e2e(project_root, test_runner, engine):
    config = 'cosmic-ray.{}.{}.conf'.format(test_runner, engine)
    session = 'adam-tests.{}.{}.session.json'.format(test_runner, engine)

    subprocess.check_call(['cosmic-ray', 'init', config, session],
                          cwd=str(project_root))
    subprocess.check_call(['cosmic-ray', 'exec', session],
                          cwd=str(project_root))

    session_path = project_root / session
    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        rate = survival_rate(work_db.work_records)
        assert rate == 0.0


def test_importing(project_root):
    config = 'cosmic-ray.import.conf'
    session = 'import_tests.session.json'

    subprocess.check_call(['cosmic-ray', 'init', config, session],
                          cwd=str(project_root))

    session_path = project_root / session
    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        rate = survival_rate(work_db.work_records)
        assert rate == 0.0


def test_empty___init__(project_root):
    config = 'cosmic-ray.empty.conf'
    session = 'empty_test.session.json'

    subprocess.check_call(['cosmic-ray', 'init', config, session],
                          cwd=str(project_root))

    session_path = project_root / session
    with use_db(str(session_path), WorkDB.Mode.open) as work_db:
        rate = survival_rate(work_db.work_records)
        assert rate == 0.0


def test_failing_baseline(project_root):
    config = 'cosmic-ray.baseline_fail.conf'
    session = 'baseline_fail.session.json'

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(['cosmic-ray', 'init', config, session],
                              cwd=str(project_root))
