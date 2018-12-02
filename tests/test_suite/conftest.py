from pathlib import Path
import sys

import pytest


@pytest.fixture
def tmpdir_path(tmpdir):
    """A temporary directory as a pathlib.Path.
    """
    return Path(str(tmpdir))


@pytest.fixture
def session(tmpdir_path):
    """A temp session file (pathlib.Path)
    """
    return tmpdir_path / 'cr-session.sqlite'


@pytest.fixture
def python_version():
    return "{}.{}".format(sys.version_info.major, sys.version_info.minor)


def pytest_addoption(parser):
    "Add our custom command line options"
    parser.addoption(
        "--e2e-engine",
        action="append",
        default=[],
        help="List of execution engines to test with.")

    parser.addoption(
        "--e2e-tester",
        action="append",
        default=[],
        help="List of test systems to use in e2e tests.")


def pytest_generate_tests(metafunc):
    "Resolve the 'engine' and 'tester' fixtures."
    if 'engine' in metafunc.fixturenames:
        metafunc.parametrize("engine",
                             set(metafunc.config.getoption('--e2e-engine')))

    if 'tester' in metafunc.fixturenames:
        metafunc.parametrize("tester",
                             set(metafunc.config.getoption('--e2e-tester')))
