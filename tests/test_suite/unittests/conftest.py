import os
from pathlib import Path

import pytest

_THIS_DIR = Path(os.path.dirname(os.path.realpath(__file__)))


@pytest.fixture
def data_dir():
    "Directory containing test data"
    return _THIS_DIR / 'data'
