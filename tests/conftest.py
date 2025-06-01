from pathlib import Path

import pytest

THIS_DIR = Path(__file__).parent


@pytest.fixture
def tmpdir_path(tmpdir):
    """A temporary directory as a pathlib.Path."""
    return Path(str(tmpdir))


@pytest.fixture(scope="session")
def resources_dirpath():
    return THIS_DIR / "resources"


@pytest.fixture
def session(tmpdir_path):
    """A temp session file (pathlib.Path)"""
    return tmpdir_path / "cr-session.sqlite"


def pytest_addoption(parser):
    "Add our custom command line options"
    parser.addoption("--e2e-distributor", action="append", default=[], help="List of distributors to test with.")

    parser.addoption("--e2e-tester", action="append", default=[], help="List of test systems to use in e2e tests.")

    parser.addoption("--run-slow", action="store_true", default=False, help="run slow tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


def pytest_generate_tests(metafunc):
    "Resolve the 'distributor' and 'tester' fixtures."
    if "distributor" in metafunc.fixturenames:
        metafunc.parametrize("distributor", set(metafunc.config.getoption("--e2e-distributor")))

    if "tester" in metafunc.fixturenames:
        metafunc.parametrize("tester", set(metafunc.config.getoption("--e2e-tester")))
