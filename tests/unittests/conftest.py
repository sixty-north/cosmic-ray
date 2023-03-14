import contextlib
import os
from pathlib import Path

import pytest

_THIS_DIR = Path(os.path.dirname(os.path.realpath(__file__)))


@pytest.fixture
def data_dir():
    "Directory containing test data"
    return _THIS_DIR / "data"


class PathUtils:
    "Path utilities for testing."

    @staticmethod
    @contextlib.contextmanager
    def excursion(directory):
        """Context manager for temporarily setting `directory` as the current working
        directory.
        """
        old_dir = os.getcwd()
        os.chdir(str(directory))
        try:
            yield
        finally:
            os.chdir(old_dir)


@pytest.fixture
def path_utils():
    "Path utilities for testing."
    return PathUtils
