"""Implementation of the 'new-config' command.
"""

import os.path

import qprompt

from cosmic_ray.config import ConfigDict
from cosmic_ray.plugins import execution_engine_names


MODULE_PATH_HELP = """The path to the module that will be mutated.

If this is a package (as opposed to a single file module),
then all modules in the package and its subpackages will be
mutated.

This path can be absolute or relative to the location of the
config file.
"""

PYTHON_VERSION_HELP = """The version of Python to use for mutation.

If provided, this should be of the form MAJOR.MINOR. If
your mutation test runs will take place on python 3.6.4,
for example, you should specify 3.6.

If blank, then the python version to us will be detected
from the system on which the init command is run.

Generally this can be blank. You need to set it if the
Python version you're using for exec is different from
that of the workers.
"""

TEST_COMMAND_HELP = """The command to execute to run the tests on mutated code.
"""


def _validate_python_version(s):
    "Return True if a string is of the form <int>.<int>, False otherwise."
    if not s:
        return True
    toks = s.split('.')
    if len(toks) != 2:
        return False
    try:
        int(toks[0])
        int(toks[1])
    except ValueError:
        return False
    return True


def new_config():
    """Prompt user for config variables and generate new config.

    Returns: A new ConfigDict.
    """
    config = ConfigDict()
    config["module-path"] = qprompt.ask_str(
        "Top-level module path",
        blk=False,
        vld=os.path.exists,
        hlp=MODULE_PATH_HELP)

    python_version = qprompt.ask_str(
        'Python version (blank for auto detection)',
        vld=_validate_python_version,
        hlp=PYTHON_VERSION_HELP)
    config['python-version'] = python_version

    timeout = qprompt.ask_str(
        'Test execution timeout (seconds)',
        vld=float,
        blk=False,
        hlp="The number of seconds to let a test run before terminating it.")
    config['timeout'] = float(timeout)
    config['excluded-modules'] = []

    config["test-command"] = qprompt.ask_str(
        "Test command",
        blk=False,
        hlp=TEST_COMMAND_HELP)

    menu = qprompt.Menu()
    for at_pos, engine_name in enumerate(execution_engine_names()):
        menu.add(str(at_pos), engine_name)
    config["execution-engine"] = ConfigDict()
    config['execution-engine']['name'] = menu.show(header="Execution engine", returns="desc")

    config["cloning"] = ConfigDict()
    config['cloning']['method'] = 'copy'
    config['cloning']['commands'] = []

    return config
