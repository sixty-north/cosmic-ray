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
    return toml.loads(sz, _dict=ConfigDict)['cosmic-ray']


def serialize_config(config):
    "Return the serialized form of `config`."
    return toml.dumps({'cosmic-ray': config})


class ConfigError(Exception):
    pass


class ConfigKeyError(ConfigError, KeyError):
    pass


class ConfigValueError(ConfigError, ValueError):
    pass


class ConfigDict(dict):
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError as exc:
            raise ConfigKeyError(*exc.args)

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
        if python_executable is None:
            python_executable = sys.executable
        return self['test-command'].format(**{'python-executable': python_executable})

    @property
    def timeout(self):
        return float(self['timeout'])

    @property
    def baseline(self):
        b = float(self['baseline'])
        if b <= 0:
            raise ConfigValueError('Baseline must be a positive value. value={}'.format(b))
        return b

    @property
    def execution_engine_name(self):
        "The name of the execution engine to use."
        return self['execution-engine']['name']

    @property
    def execution_engine_config(self):
        "The configuation for the named execution engine."
        name = self.execution_engine_name
        return self['execution-engine'].get(name, ConfigDict())


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
