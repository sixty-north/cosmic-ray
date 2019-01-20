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


def deserialize_config(sz):
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

    def test_command(self, python_executable=None):
        """Get the command to run to execute tests.

        Args:
            python_executable: The Python executable to use if the command string
                needs it. If this is not provided, it defaults to `sys.executable`.
        """
        if python_executable is None:
            python_executable = sys.executable
        return self['test-command'].format(**{'python-executable': python_executable})

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


def get_db_name(session_name):
    """Determines the filename for a session.

    Basically, if `session_name` ends in ".sqlite" this return `session_name`
    unchanged. Otherwise it return `session_name` with ".sqlite" added to the
    end.
    """
    if session_name.endswith('.sqlite'):
        return session_name
    return '{}.sqlite'.format(session_name)
