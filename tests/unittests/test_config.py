"""Tests for config loading functions."""

import io
from unittest import mock

import pytest

from cosmic_ray.config import ConfigDict, ConfigError, load_config, serialize_config


def test_load_valid_stdin():
    temp_stdin = io.StringIO()
    temp_stdin.name = "stringio"
    config = ConfigDict()
    config["key"] = "value"
    temp_stdin.write(serialize_config(config))
    temp_stdin.seek(0)
    with mock.patch("cosmic_ray.config.sys.stdin", temp_stdin):
        assert load_config()["key"] == "value"


def test_load_invalid_stdin_raises_ConfigError():
    temp_stdin = io.StringIO()
    temp_stdin.name = "stringio"
    temp_stdin.write("{invalid")
    temp_stdin.seek(0)

    with mock.patch("cosmic_ray.config.sys.stdin", temp_stdin):
        with pytest.raises(ConfigError):
            load_config()


def test_load_from_valid_config_file(tmpdir):
    config_path = tmpdir / "config.conf"
    config = ConfigDict()
    config["key"] = "value"
    with config_path.open(mode="wt", encoding="utf-8") as handle:
        handle.write(serialize_config(config))
    assert load_config(str(config_path))["key"] == "value"


def test_load_non_existent_file_raises_ConfigError():
    with pytest.raises(ConfigError):
        load_config("/foo/bar/this/does/no-exist/I/hope")


def test_load_from_invalid_config_file_raises_ConfigError(tmpdir):
    config_path = tmpdir / "config.yml"
    with config_path.open(mode="wt", encoding="utf-8") as handle:
        handle.write("{asdf")
    with pytest.raises(ConfigError):
        load_config(str(config_path))


def test_load_from_non_utf8_file_raises_ConfigError(tmpdir):
    config_path = tmpdir / "config.conf"
    config = {"key": "value"}
    with config_path.open(mode="wb") as handle:
        handle.write(serialize_config(config).encode("utf-16"))
    with pytest.raises(ConfigError):
        load_config(str(config_path))


def test_mutation_order_and_limit_properties():
    """Test the mutation_order and mutation_limit properties of ConfigDict."""
    # Test default values
    config = ConfigDict()
    assert config.mutation_order == 1
    assert config.mutation_limit is None
    assert config.disable_overlapping_mutations is True  # Default is True

    # Test with explicitly set values
    config = ConfigDict({"mutation-order": 3, "mutation-limit": 100, "disable-overlapping-mutations": False})
    assert config.mutation_order == 3
    assert config.mutation_limit == 100
    assert config.disable_overlapping_mutations is False

    # Test with string values (should be converted properly)
    config = ConfigDict({"mutation-order": "2", "mutation-limit": "50"})
    assert config.mutation_order == 2
    assert config.mutation_limit == 50

    # Test with mutation-limit set to None explicitly
    config = ConfigDict({"mutation-order": 4, "mutation-limit": None, "disable-overlapping-mutations": True})
    assert config.mutation_order == 4
    assert config.mutation_limit is None
    assert config.disable_overlapping_mutations is True
