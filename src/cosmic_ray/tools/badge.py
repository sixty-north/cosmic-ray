import os
from logging import getLogger

import docopt
from anybadge import Badge

from cosmic_ray.config import ConfigDict, load_config
from cosmic_ray.tools.survival_rate import survival_rate
from cosmic_ray.work_db import use_db, WorkDB

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

        badge = Badge(
            label=config.badge_label,
            value=percent,
            value_format=config.badge_format,
            thresholds=config.badge_thresholds,
        )

        log.info(("Generating badge: " + config.badge_format) % percent)

        try:
            os.unlink(badge_filename)
        except OSError:
            pass

        badge.write_badge(badge_filename)
