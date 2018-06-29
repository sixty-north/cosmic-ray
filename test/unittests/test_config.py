"""Tests for config loading functions.
"""
import io

import pytest

from cosmic_ray.config import load_config
from kfg.config import ConfigError


def test_load_valid_stdin(mocker):
    temp_stdin = io.StringIO()
    temp_stdin.name = 'stringio'
    temp_stdin.write('{key: value}')
    temp_stdin.seek(0)
    mocker.patch('sys.stdin', temp_stdin)

    assert load_config()['key'] == 'value'


def test_load_invalid_stdin_raises_ConfigError(mocker):
    temp_stdin = io.StringIO()
    temp_stdin.name = 'stringio'
    temp_stdin.write('{invalid')
    temp_stdin.seek(0)
    mocker.patch('sys.stdin', temp_stdin)

    with pytest.raises(ConfigError):
        load_config()


def test_load_from_valid_config_file(tmpdir):
    config_path = tmpdir / 'config.yml'
    with config_path.open(mode='wt', encoding='utf-8') as handle:
        handle.write('{key: value}')
    assert load_config(str(config_path))['key'] == 'value'


def test_load_non_existent_file_raises_ConfigError():
    with pytest.raises(ConfigError):
        load_config('/foo/bar/this/does/no-exist/I/hope')


def test_load_from_invalid_config_file_raises_ConfigError(tmpdir):
    config_path = tmpdir / 'config.yml'
    with config_path.open(mode='wt', encoding='utf-8') as handle:
        handle.write('{asdf')
    with pytest.raises(ConfigError):
        load_config(str(config_path))


def test_load_from_non_utf8_file_raises_ConfigError(tmpdir):
    config_path = tmpdir / 'config.yml'
    with config_path.open(mode='wb') as handle:
        handle.write('{key: value}'.encode('utf-16'))
    with pytest.raises(ConfigError):
        load_config(str(config_path))
