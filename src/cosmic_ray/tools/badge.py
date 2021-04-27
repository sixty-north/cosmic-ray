"""Tool for creating badge.
"""
import os
from logging import getLogger

from anybadge import Badge

import click
from cosmic_ray.config import load_config
from cosmic_ray.tools.survival_rate import survival_rate
from cosmic_ray.work_db import WorkDB, use_db

log = getLogger()


@click.command()
@click.argument("config_file", type=click.Path(exists=True, dir_okay=False, readable=True))
@click.argument("badge_file", type=click.Path(dir_okay=False, writable=True))
@click.argument("session_file", type=click.Path(exists=True, dir_okay=False, readable=True))
def generate_badge(config_file, badge_file, session_file):
    """Generate badge file."""

    with use_db(session_file, WorkDB.Mode.open) as db:
        config = load_config(config_file)

        percent = 100 - survival_rate(db)

        config = config["badge"]

        badge = Badge(
            label=config["label"],
            value=percent,
            value_format=config["format"],
            thresholds=config["thresholds"],
        )

        log.info("Generating badge: " + config["format"], percent)  # pylint: disable=logging-not-lazy

        try:
            os.unlink(badge_file)
        except OSError:
            pass

        badge.write_badge(badge_file)
