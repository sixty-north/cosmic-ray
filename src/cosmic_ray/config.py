"""Configuration module."""
from contextlib import contextmanager
import logging
import sys

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
        raise ConfigError(
            'Error loading configuration from {}'.format(filename)) from exc


def deserialize_config(sz) -> 'ConfigDict':
    "Parse a serialized config into a ConfigDict."
    return toml.loads(sz, _dict=ConfigDict)['cosmic-ray']


def serialize_config(config):
    "Return the serialized form of `config`."
    return toml.dumps({'cosmic-ray': config})


class ConfigError(Exception):
    "Base class for exceptions raised by ConfigDict."


class ConfigKeyError(ConfigError, KeyError):
    "KeyError subclass raised by ConfigDict."


class ConfigValueError(ConfigError, ValueError):
    "ValueError subclass raised by ConfigDict."


class ConfigDict(dict):
    """A dictionary subclass that contains the application configuration.
    """
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
    def python_version(self):
        """Get the configured Python version.

        If this is not set in the config, then it defaults to the version of the current runtime.

        Returns: A string of the form "MAJOR.MINOR", e.g. "3.6".
        """
        v = self.get('python-version', '')
        if v == '':
            v = "{}.{}".format(sys.version_info.major, sys.version_info.minor)
        return v

    @property
    def test_command(self):
        """The command to run to execute tests.
        """
        return self['test-command']

    @property
    def timeout(self):
        "The timeout (seconds) for tests."
        return float(self['timeout'])

    @property
    def execution_engine_name(self):
        "The name of the execution engine to use."
        return self['execution-engine']['name']

    @property
    def execution_engine_config(self):
        "The configuration for the named execution engine."
        name = self.execution_engine_name
        return self['execution-engine'].get(name, ConfigDict())

    @property
    def cloning_config(self):
        "The 'cloning' section of the config."
        return self['cloning']

    @property
    def badge(self):
        return self['badge']

    @property
    def badge_label(self):
        return self.badge['label']

    @property
    def badge_format(self):
        return self.badge['format']

    @property
    def badge_thresholds(self):
        return self.badge['thresholds']


@contextmanager
def _config_stream(filename):
    """Given a configuration's filename, this returns a stream from which a configuration can be read.

    If `filename` is `None` or '-' then stream will be `sys.stdin`. Otherwise,
    it's the open file handle for the filename.
    """
    if filename is None or filename == '-':
        log.info('Reading config from stdin')
        yield sys.stdin
    else:
        with open(filename, mode='rt') as handle:
            log.info('Reading config from %r', filename)
            yield handle
