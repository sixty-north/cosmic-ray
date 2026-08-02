"""Implementation of the 'new-config' command."""

import os.path

import click

from cosmic_ray.config import ConfigDict
from cosmic_ray.plugins import distributor_names

MODULE_PATH_HELP = """The path to the module that will be mutated.

If this is a package (as opposed to a single file module),
then all modules in the package and its subpackages will be
mutated.

This path can be absolute or relative to the location of the
config file.
"""


TEST_COMMAND_HELP = """The command to execute to run the tests on mutated code.
"""


def new_config():
    """Prompt user for config variables and generate new config.

    Returns: A new ConfigDict.
    """
    config = ConfigDict()
    click.echo(MODULE_PATH_HELP)
    config["module-path"] = click.prompt(
        "Top-level module path",
        type=click.Path(exists=True, path_type=str),
    )

    timeout = click.prompt(
        "Test execution timeout (seconds)",
        type=float,
        show_default=False,
    )
    config["timeout"] = timeout
    config["excluded-modules"] = []

    click.echo(TEST_COMMAND_HELP)
    config["test-command"] = click.prompt("Test command", type=str)

    distributors = sorted(distributor_names())
    config["distributor"] = ConfigDict()
    config["distributor"]["name"] = click.prompt("Distributor", type=click.Choice(distributors, case_sensitive=True))

    return config
