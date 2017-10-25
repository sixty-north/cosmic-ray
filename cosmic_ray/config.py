import sys
import yaml


def load_config(filename=None):
    if filename is None:
        return yaml.load(sys.stdin)

    with open(filename, mode='rt') as f:
        return yaml.load(f)


def serialize_config(config):
    return yaml.dump(config)


def get_db_name(session_name):
    if session_name.endswith('.json'):
        return session_name
    else:
        return '{}.json'.format(session_name)


class ConfigError(Exception):
    pass
