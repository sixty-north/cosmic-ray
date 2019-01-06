"""Support for making clones of projects for test isolation.
"""

import contextlib
import logging
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import venv

import git

log = logging.getLogger(__name__)


@contextlib.contextmanager
def cloned_workspace(clone_config, chdir=True):
    """Create a cloned workspace and yield it.

    This creates a workspace for a with-block and cleans it up on exit. By
    default, this will also change to the workspace's `clone_dir` for the
    duration of the with-block.

    Args:
        clone_config: The execution engine configuration to use for the workspace.
        chdir: Whether to change to the workspace's `clone_dir` before entering the with-block.

    Yields: The `CloneWorkspace` instance created for the context.
    """
    workspace = ClonedWorkspace(clone_config)
    original_dir = os.getcwd()
    if chdir:
        os.chdir(workspace.clone_dir)

    try:
        yield workspace
    finally:
        os.chdir(original_dir)
        workspace.cleanup()


class ClonedWorkspace:
    """Clone a project and install it into a temporary virtual environment.
    """

    def __init__(self, clone_config):
        self._tempdir = tempfile.TemporaryDirectory()
        log.info('New project clone in %s', self._tempdir.name)

        self._clone_dir = str(Path(self._tempdir.name) / 'repo')

        if clone_config['method'] == 'git':
            clone_with_git(
                clone_config.get('repo-uri', '.'),
                self._clone_dir)
        elif clone_config['method'] == 'copy':
            clone_with_copy(
                os.getcwd(),
                self._clone_dir)

        # pylint: disable=fixme
        # TODO: We should allow user to specify which version of Python to use.
        # How? The EnvBuilder could be passed a path to a python interpreter
        # which is used in the call to pip. This path would need to come from
        # the config.

        # Install into venv
        venv_path = Path(self._tempdir.name) / 'venv'
        log.info('Creating virtual environment in %s', venv_path)
        builder = EnvBuilder(self._clone_dir,
                             clone_config.get('extras', ()))
        context = builder.create_with_context(venv_path)

        self._python_executable = context.env_exe  # pylint: disable=no-member

    @property
    def clone_dir(self):
        "The root of the cloned project."
        return self._clone_dir

    @property
    def python_executable(self):
        "The python executable of the virtual environment"
        return self._python_executable

    def cleanup(self):
        "Remove the directory containin the clone and virtual environment."
        log.info('Removing temp dir %s', self._tempdir.name)
        self._tempdir.cleanup()


def clone_with_git(repo_uri, dest_path):
    """Create a clone by cloning a git repository.

    Args:
        repo_uri: The URI of the git repository to clone.
        dest_path: The location to clone to.
    """
    log.info('Cloning git repo %s to %s', repo_uri, dest_path)
    git.Repo.clone_from(repo_uri, dest_path, depth=1)


def clone_with_copy(src_path, dest_path):
    """Clone a directory try by copying it.

    Args:
        src_path: The directory to be copied.
        dest_path: The location to copy the directory to.
    """
    log.info('Cloning directory tree %s to %s', src_path, dest_path)
    shutil.copytree(src_path, dest_path)


class EnvBuilder(venv.EnvBuilder):
    """EnvBuilder that installs a project and any specified extras.
    """

    def __init__(self, repo_dir, commands, *args, **kwargs):
        super().__init__(self, with_pip=True, symlinks=True, *args, **kwargs)
        self.repo_dir = repo_dir
        self._context = None

        self.commands = tuple(commands)

    def create_with_context(self, env_dir):
        """Call create() and return the context.
        """
        assert self._context is None

        super().create(str(env_dir))

        # A bit if a hack. We remember the context seen in a call to
        # `post_setup()` and return it here.
        assert self._context is not None
        return self._context

    def post_setup(self, context):
        self._context = context

        for command in self.commands:
            log.info('Running installation command: %s', command)
            subprocess.run(command.split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           cwd=self.repo_dir,
                           check=True)
