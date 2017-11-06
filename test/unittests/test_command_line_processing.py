import os

import pytest

import cosmic_ray.cli


def test_invalid_command_line_returns_EX_USAGE():
    with pytest.raises(SystemExit) as exc:
        cosmic_ray.cli.main(['init', 'foo'])

    assert exc.value.code == os.EX_USAGE
