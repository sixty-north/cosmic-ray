"Implementation of the 'new-config' command."

import qprompt

from cosmic_ray.config import ConfigDict
from cosmic_ray.plugins import execution_engine_names


def new_config():
    """Prompt user for config variables and generate new config.

    Returns: A new ConfigDict.
    """
    config = ConfigDict()
    config["module-path"] = qprompt.ask_str("Top-level module path")

    python_version = qprompt.ask_str(
        'Python version (blank for auto detection)')
    config['python-version'] = python_version

    timeout = qprompt.ask_str('Test execution timeout (seconds)')
    config['timeout'] = float(timeout)
    config['excluded-modules'] = []

    config["test-command"] = qprompt.ask_str("Test command")

    menu = qprompt.Menu()
    for at_pos, engine_name in enumerate(execution_engine_names()):
        menu.add(str(at_pos), engine_name)
    config["execution-engine"] = ConfigDict()
    config['execution-engine']['name'] = menu.show(header="Execution engine", returns="desc")

    config["cloning"] = ConfigDict()
    config['cloning']['method'] = 'copy'
    config['cloning']['commands'] = []

    return config
