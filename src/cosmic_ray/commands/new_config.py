"""Implementation of the 'new-config' command.
"""

import os.path

import qprompt

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
    config["module-path"] = qprompt.ask_str(
        "Top-level module path", blk=False, vld=os.path.exists, hlp=MODULE_PATH_HELP
    )

    timeout = qprompt.ask_str(
        "Test execution timeout (seconds)",
        vld=float,
        blk=False,
        hlp="The number of seconds to let a test run before terminating it.",
    )
    config["timeout"] = float(timeout)
    config["excluded-modules"] = []

    config["test-command"] = qprompt.ask_str("Test command", blk=False, hlp=TEST_COMMAND_HELP)

    menu = qprompt.Menu()
    for at_pos, distributor_name in enumerate(distributor_names()):
        menu.add(str(at_pos), distributor_name)
    config["distributor"] = ConfigDict()
    config["distributor"]["name"] = menu.show(header="Distributor", returns="desc")

    return config
