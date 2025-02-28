"""Implementation of the 'new-config' command."""

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

    mutation_order = qprompt.ask_str(
        "Mutation order (default: 1)",
        vld=lambda x: int(x) > 0,
        dflt="1",
        blk=False,
        hlp="The maximum number of mutations to apply in a single test run. 1 means only first-order mutants, higher values enable higher-order mutants.",
    )
    config["mutation-order"] = int(mutation_order)

    specific_order = qprompt.ask_str(
        "Specific mutation order (default: all orders up to maximum)",
        vld=lambda x: x == "" or (int(x) > 0 and int(x) <= int(mutation_order)),
        dflt="",
        blk=True,
        hlp="If specified, only generate mutations of exactly this order. Must be less than or equal to the maximum mutation order.",
    )
    if specific_order:
        config["specific-order"] = int(specific_order)

    mutation_limit = qprompt.ask_str(
        "Mutation limit (default: unlimited)",
        vld=lambda x: x == "" or int(x) > 0,
        dflt="",
        blk=True,
        hlp="The maximum number of mutations to generate. Useful for higher-order mutations which can grow exponentially. When specified, mutations will be selected randomly.",
    )
    if mutation_limit:
        config["mutation-limit"] = int(mutation_limit)

    disable_overlapping = qprompt.ask_str(
        "Disable overlapping mutations (default: True)",
        vld=bool,
        dflt=True,
        hlp="If enabled (default), higher-order mutants will not include mutations that target the same code location, which could lead to mutations canceling each other out.",
    )
    config["disable-overlapping-mutations"] = disable_overlapping

    config["test-command"] = qprompt.ask_str("Test command", blk=False, hlp=TEST_COMMAND_HELP)

    menu = qprompt.Menu()
    for at_pos, distributor_name in enumerate(distributor_names()):
        menu.add(str(at_pos), distributor_name)
    config["distributor"] = ConfigDict()
    config["distributor"]["name"] = menu.show(header="Distributor", returns="desc")

    return config
