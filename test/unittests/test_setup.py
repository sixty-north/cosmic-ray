import importlib.util
from pathlib import Path

from setuptools import find_packages


def test_packages(mocker):
    """Test that PACKAGES in setup.py is what find_packages returns."""
    setup_py = Path(__file__).parents[2] / 'setup.py'

    spec = importlib.util.spec_from_file_location('module.name', str(setup_py))
    setup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(setup)

    assert setup.PACKAGES == sorted(find_packages())
