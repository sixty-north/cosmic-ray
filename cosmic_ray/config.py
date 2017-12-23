"""Configuration module."""
from contextlib import contextmanager
import logging
import sys

import yaml

log = logging.getLogger()


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
            return yaml.safe_load(handle)
    except (OSError, UnicodeDecodeError, yaml.parser.ParserError) as exc:
        raise ConfigError(
            'Error loading configuration from {}'.format(filename)) from exc


def serialize_config(config):
    """Convert a configuration dict into a string.

    This is complementary with `load_config`.
    """
    return yaml.dump(config)


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
