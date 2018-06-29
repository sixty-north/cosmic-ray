"""Configuration module."""
from contextlib import contextmanager
import logging
import sys

import kfg.config
import kfg.yaml

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


class Config(kfg.config.Config):
    """kfg.config.Config subclass for Cosmic Ray.

    The primary job of this subclass is to configure the transforms for CR's
    configuration.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_transform('timeout', float)
        self.set_transform('baseline', self._positive_float)

    @staticmethod
    def _positive_float(x):
        x = float(x)
        if x <= 0:
            raise ValueError('positive float expected. value={}'.format(x))
        return x


def load_config(filename=None):
    """Load a configuration from a file or stdin.

    If `filename` is `None`, then configuration gets read from stdin.

    Returns: A configuration dict.

    Raises:
      kfg.config.ConfigError: If there is an error loading the config.
    """
    try:
        with _config_stream(filename) as handle:
            filename = handle.name
            return kfg.yaml.load_config(handle, config=Config())
    except (OSError, ValueError) as exc:
        raise kfg.config.ConfigError(
            'Error loading configuration from {}'.format(filename)) from exc


def serialize_config(config):
    return kfg.yaml.serialize_config(config)


def get_db_name(session_name):
    """Determines the filename for a session.

    Basically, if `session_name` ends in ".json" this return `session_name`
    unchanged. Otherwise it return `session_name` with ".json" added to the
    end.
    """
    if session_name.endswith('.json'):
        return session_name
    return '{}.json'.format(session_name)
