"""Configuration module."""

import logging
import sys
from contextlib import contextmanager

import toml

log = logging.getLogger()


def load_config(filename=None):
    """Load a configuration from a file or stdin.

    If `filename` is `None` or "-", then configuration gets read from stdin.

    Returns: A `ConfigDict`.

    Raises: ConfigError: If there is an error loading the config.
    """
    try:
        with _config_stream(filename) as handle:
            filename = handle.name
            return deserialize_config(handle.read())
    except (OSError, toml.TomlDecodeError, UnicodeDecodeError) as exc:
        raise ConfigError(f"Error loading configuration from {filename}") from exc


def deserialize_config(sz) -> "ConfigDict":
    "Parse a serialized config into a ConfigDict."
    return toml.loads(sz, _dict=ConfigDict)["cosmic-ray"]


def serialize_config(config):
    "Return the serialized form of `config`."
    return toml.dumps({"cosmic-ray": config})


class ConfigError(Exception):
    "Base class for exceptions raised by ConfigDict."


class ConfigKeyError(ConfigError, KeyError):
    "KeyError subclass raised by ConfigDict."


class ConfigValueError(ConfigError, ValueError):
    "ValueError subclass raised by ConfigDict."


class ConfigDict(dict):
    """A dictionary subclass that contains the application configuration."""

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError as exc:
            raise ConfigKeyError(*exc.args)

    def sub(self, *segments):
        "Get a sub-configuration."
        d = self
        for segment in segments:
            try:
                d = d[segment]
            except KeyError:
                return ConfigDict({})
        return d

    @property
    def test_command(self):
        """The command to run to execute tests."""
        return self["test-command"]

    @property
    def timeout(self):
        "The timeout (seconds) for tests."
        return float(self["timeout"])

    @property
    def distributor_name(self):
        "The name of the distributor to use."
        return self["distributor"]["name"]

    @property
    def distributor_config(self):
        "The configuration for the named distributor."
        name = self.distributor_name
        return self["distributor"].get(name, ConfigDict())

    @property
    def operators_config(self):
        """The configuration for specified operators.

        This is a dict mapping operator names to dicts which represent keyword-arguments
        for parameterizing an operator. Each keyword arg dict is a single parameterization
        of the operator, and each parameterized operator will be executed once for each
        parameterization.
        """
        return self.get("operators", {})
        
    @property
    def mutation_order(self):
        """The order of mutations to apply (how many mutations per work item).
        
        If not specified or set to 1, only first-order mutants will be created.
        Higher values result in applying multiple mutations in a single test run.
        """
        return int(self.get("mutation-order", 1))
        
    @property
    def mutation_limit(self):
        """The maximum number of mutations to generate.
        
        If not specified, all possible mutations will be generated.
        When specified, only a random subset of mutations will be selected.
        This is particularly useful for higher-order mutations which can grow exponentially.
        """
        limit = self.get("mutation-limit", None)
        return int(limit) if limit is not None else None


@contextmanager
def _config_stream(filename):
    """Given a configuration's filename, this returns a stream from which a configuration can be read.

    If `filename` is `None` or '-' then stream will be `sys.stdin`. Otherwise,
    it's the open file handle for the filename.
    """
    if filename is None or filename == "-":
        log.info("Reading config from stdin")
        yield sys.stdin
    else:
        with open(filename) as handle:
            log.info("Reading config from %r", filename)
            yield handle
