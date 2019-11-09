"""Tool for creating badge.
"""
import os
from logging import getLogger

from anybadge import Badge

import docopt
from cosmic_ray.config import load_config
from cosmic_ray.tools.survival_rate import survival_rate
from cosmic_ray.work_db import WorkDB, use_db

log = getLogger()


def generate_badge():
    """cr-badge

Usage: cr-badge [--config <config_file>]  <badge_file> <session-file>

Generate badge file.

options:
    --config <config_file> Configuration file to use instead of session configuration
"""

    arguments = docopt.docopt(generate_badge.__doc__, version='cr-format 0.1')
    config_file = arguments['--config']
    badge_filename = arguments['<badge_file>']

    with use_db(arguments['<session-file>'], WorkDB.Mode.open) as db:
        assert isinstance(db, WorkDB)
        if config_file:
            config = load_config(config_file)
        else:
            config = db.get_config()

        percent = 100 - survival_rate(db)

        config = config['badge']

        badge = Badge(
            label=config['label'],
            value=percent,
            value_format=config['format'],
            thresholds=config['thresholds'],
        )

        log.info("Generating badge: " + config['format'], percent)  # pylint: disable=logging-not-lazy

        try:
            os.unlink(badge_filename)
        except OSError:
            pass

        badge.write_badge(badge_filename)
