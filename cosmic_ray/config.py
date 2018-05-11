"""Configuration module."""
from contextlib import contextmanager
import logging
import sys

import yaml

log = logging.getLogger()


class Config:
    "Simple interface to a Cosmic Ray configuration."

    def __init__(self, cfg):
        self._cfg = cfg

    def __getitem__(self, path):
        """Get a config item by its path.

        Args:
            path: An iterable of strings defining the path to the item to get.

        Returns: The config element at `path`.

        Raises:
            ConfigError: The path is not in the config.

        """
        if not isinstance(path, tuple):
            path = (path,)

        try:
            cfg = self._cfg
            for step in path:
                cfg = cfg[step]
            return cfg 
        except KeyError:
            raise ConfigPathError(*path)

    def get(self, *path, default=None):
        """Get a config item by its path, or `default`.

        Args:
            path: An iterable of strings defining the path to the item to get.

        Returns: The config element at `path`. If there is no item at that
            path, this returns `default`.
        """
        try:
            return self[path]
        except ConfigError:
            return default

    def __contains__(self, path):
        try:
            _ = self.__getitem__(path)
            return True
        except ConfigError:
            return False

    def as_dict(self):
        return self._cfg


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


def load_config(filename=None):
    """Load a configuration from a file or stdin.

    If `filename` is `None`, then configuration gets read from stdin.

    Returns: A configuration dict.

    Raises:
      ConfigError: If there is an error loading the config.
    """
    try:
        with _config_stream(filename) as handle:
            filename = handle.name
            return Config(yaml.safe_load(handle))
    except (OSError, UnicodeDecodeError, yaml.parser.ParserError) as exc:
        raise ConfigError(
            'Error loading configuration from {}'.format(filename)) from exc


def serialize_config(config):
    """Convert a configuration dict into a string.

    This is complementary with `load_config`.
    """
    return yaml.dump(config.as_dict())


def get_db_name(session_name):
    """Determines the filename for a session.

    Basically, if `session_name` ends in ".json" this return `session_name`
    unchanged. Otherwise it return `session_name` with ".json" added to the
    end.
    """
    if session_name.endswith('.json'):
        return session_name
    return '{}.json'.format(session_name)


class ConfigError(Exception):
    """Errors loading configs or with values in a config."""
    pass


class ConfigPathError(ConfigError):
    """Indicates that path was not found in a config.
    """
    def __init__(self, *path):
        self._path = tuple(path)
        super().__init__('Missing config value: {}'.format(self.path))

    @property
    def path(self):
        "The path that was not found."
        return self._path


class ConfigValueError(ConfigError):
    """Indicates that the values found in a config have invalid values.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
