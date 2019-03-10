"""Support for making clones of projects for test isolation.
"""

import contextlib
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

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
        self._venv_path = Path(self._tempdir.name) / 'venv'
        log.info('Creating virtual environment in %s', self._venv_path)
        _build_env(self._venv_path)

        for command in clone_config.get('commands', ()):
            command = self.replace_variables(command)
            log.info('Running installation command: %s', command)
            try:
                # TODO: How to we execute this in the environment of the venv we just created?
                r = subprocess.run(command.split(),
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   cwd=self._clone_dir,
                                   check=True)

                log.info('Command results: %s', r.stdout)
            except subprocess.CalledProcessError as exc:
                log.error("Error running command in virtual environment\ncommand: %s\nerror: %s",
                          command, exc.output)

    @property
    def clone_dir(self):
        "The root of the cloned project."
        return self._clone_dir

    def replace_variables(self, text):
        """Replace variable placeholders in `text` with values from the virtual env.

        The variables are:
          - {python-executable}

        Args:
            text: The text to do replacment int.

        Returns: The text after replacement.
        """
        variables = {
            'python-executable': str(self._venv_path / 'bin' / 'python')
        }
        return text.format(**variables)

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


def _build_env(venv_dir):
    """Create a new virtual environment in `venv_dir`.

    This uses the base prefix of any virtual environment that you may be using
    when you call this.
    """
    # NB: We had to create the because the venv modules wasn't doing what we
    # needed. In particular, if we used it create a venv from an existing venv,
    # it *always* created symlinks back to the original venv's python
    # executables. Then, when you used those linked executables, you ended up
    # interacting with the original venv. I could find no way around this, hence
    # this function.
    prefix = getattr(sys, 'real_prefix', sys.prefix)
    python = Path(prefix) / 'bin' / 'python'
    command = '{} -m venv {}'.format(python, venv_dir)
    try:
        log.info('Creating virtual environment: %s', command)
        subprocess.run(command.split(),
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       check=True)
    except subprocess.CalledProcessError as exc:
        log.error("Error creating virtual environment: %s", exc.output)
        raise
