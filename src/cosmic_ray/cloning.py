"""Support for making clones of projects for test isolation.
"""
import abc
import logging
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Type

import virtualenv

import git

from cosmic_ray.exceptions import CosmicRayTestingException as Exc

log = logging.getLogger(__name__)


class WorkspaceMeta(type):
    _registred = {}

    def __new__(cls, *args, **kwargs):
        new_class = super(WorkspaceMeta, cls).__new__(cls, *args, **kwargs)  # type: Type[Workspace]
        cls._registred[new_class.name] = new_class
        return new_class

    @classmethod
    def get_workspace_class(cls, name):
        return cls._registred[name]


class Workspace(metaclass=WorkspaceMeta):
    name = None

    @classmethod
    def get_workspace(cls, name, clone_config) -> 'Workspace':
        return type(cls).get_workspace_class(name)(clone_config)

    @abc.abstractmethod
    def cleanup(self):
        pass

    @property
    @abc.abstractmethod
    def clone_dir(self):
        pass


class ClonedWorkspace(Workspace):
    """Clone a project into a temporary directory.
    """
    name = 'cloned'

    def __init__(self, clone_config):
        self._tempdir = tempfile.TemporaryDirectory()
        self._prepare_directory(clone_config)
        self._load_environment()
        self._run_commands(clone_config.get('commands', ()))

    def _prepare_directory(self, clone_config):
        log.info('New project clone in %s', self._tempdir.name)
        self._clone_dir = str(Path(self._tempdir.name) / 'repo')

        method = clone_config['method']
        if method == 'git':
            _clone_with_git(
                clone_config.get('repo-uri', '.'),
                self._clone_dir)

        elif method == 'copy':
            _clone_with_copy(
                os.getcwd(),
                self._clone_dir)

        else:
            raise Exception("Clone method '%s' unknown" % method)

    def _load_environment(self):
        os.environ['PYTHONPATH'] = \
            '%s:%s' % (self.clone_dir, os.environ.get('PYTHONPATH', ''))

    @property
    def clone_dir(self):
        "The root of the cloned project."
        return self._clone_dir

    def cleanup(self):
        "Remove the directory containin the clone and virtual environment."
        log.info('Removing temp dir %s', self._tempdir.name)
        self._tempdir.cleanup()

    def _run_commands(self, commands):
        """Run a set of commands in the workspace's virtual environment.

        Args:
            commands: An iterable of strings each representing a command to be executed.
        """
        for command in commands:
            log.info('Running installation command: %s', command)
            try:
                r = subprocess.run(command,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   shell=True,
                                   cwd=str(self._clone_dir),
                                   check=True)

                log.info('Command results: %s', r.stdout)
            except subprocess.CalledProcessError as exc:
                log.error("Error running command in virtual environment\ncommand: %s\nerror: %s",
                          command, exc.output)


class ClonedWorkspaceWithVirtualenv(ClonedWorkspace):
    """Clone a project and install it into a temporary virtual environment.

    Note that this actually *activates* the virtual environment, so don't construct one
    of these unless you want that to happen in your process.
    """
    name = 'cloned_with_virtualenv'

    def _prepare_directory(self, clone_config):
        # pylint: disable=fixme
        # TODO: We should allow user to specify which version of Python to use.
        # How? The EnvBuilder could be passed a path to a python interpreter
        # which is used in the call to pip. This path would need to come from
        # the config.

        # Install into venv
        self._venv_path = Path(self._tempdir.name) / 'venv'
        log.info('Creating virtual environment in %s', self._venv_path)
        virtualenv.create_environment(str(self._venv_path))

    def _load_environment(self):
        _activate(self._venv_path)
        _install_sitecustomize(self._venv_path)


def _clone_with_git(repo_uri, dest_path):
    """Create a clone by cloning a git repository.

    Args:
        repo_uri: The URI of the git repository to clone.
        dest_path: The location to clone to.
    """
    log.info('Cloning git repo %s to %s', repo_uri, dest_path)
    git.Repo.clone_from(repo_uri, dest_path, depth=1)


def _clone_with_copy(src_path, dest_path):
    """Clone a directory try by copying it.

   Args:
        src_path: The directory to be copied.
        dest_path: The location to copy the directory to.
    """
    log.info('Cloning directory tree %s to %s', src_path, dest_path)
    shutil.copytree(src_path, dest_path)


def _activate(venv_path):
    """Activate a virtual environment in the current process.

    This assumes a virtual environment that has a "activate_this.py" script, e.g.
    one created with `virtualenv` and *not* `venv`.

    Args:
        venv_path: Path of virtual environment to activate.
    """
    _home_dir, _lib_dir, _inc_dir, bin_dir = virtualenv.path_locations(str(venv_path))
    activate_script = str(Path(bin_dir) / 'activate_this.py')

    # This is the recommended way of activating venvs in a program:
    # https://virtualenv.pypa.io/en/stable/userguide/#using-virtualenv-without-bin-python
    exec(open(activate_script).read(), {'__file__': activate_script})  # pylint: disable=exec-used


_SITE_CUSTOMIZE = """
class {0}(Exception):
    pass

__builtins__['{0}'] = {0}
""".format(Exc.__name__)


def _install_sitecustomize(venv_path):
    _home_dir, lib_dir, _inc_dir, _bin_dir = virtualenv.path_locations(str(venv_path))
    with open(str(Path(lib_dir) / 'site-packages' / 'sitecustomize.py'), mode='wt', encoding='utf-8') as sc:
        sc.write(_SITE_CUSTOMIZE)
