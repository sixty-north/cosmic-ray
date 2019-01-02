"""Support for making clones of projects for test isolation.
"""

import contextlib
import logging
import os
from pathlib import Path
import subprocess
import tempfile
import venv

import git

log = logging.getLogger(__name__)


@contextlib.contextmanager
def cloned_workspace(engine_config, chdir=True):
    """Create a cloned workspace and yield it.

    This creates a workspace for a with-block and cleans it up on exit. By
    default, this will also change to the workspace's `clone_dir` for the
    duration of the with-block. 

    Args:
        engine_config: The execution engine configuration to use for the workspace.
        chdir: Whether to change to the workspace's `clone_dir` before entering the with-block.

    Yields: The `CloneWorkspace` instance created for the context.
    """
    workspace = ClonedWorkspace(engine_config)
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
    def __init__(self, engine_config):
        # TODO: Rather than passing in the engine_config, perhaps the config
        # should have a notion of a "code base" section which describes how to
        # clone the project in an engine-independent way. It could specify git,
        # file copy, svn, or whatever, along with the relevant paths/URIs/etc.

        self._tempdir = tempfile.TemporaryDirectory()
        log.info('New project clone in %s', self._tempdir.name)

        self._clone_dir = str(Path(self._tempdir.name) / 'repo')

        # Clone repo. Currently just with git, but could expand it later.
        repo_uri = engine_config.get('repo-uri', '.')
        log.info('Cloning git repo %s to %s', repo_uri, self._clone_dir)
        git.Repo.clone_from(repo_uri, self._clone_dir, depth=1)

        # TODO: We should allow user to specify which version of Python to use.
        # How? The EnvBuilder could be passed a path to a python interpreter
        # which is used in the call to pip. This path would need to come from
        # the config.

        # Install into venv
        venv_path = Path(self._tempdir.name) / 'venv'
        log.info('Creating virtual environment in %s', venv_path)
        builder = EnvBuilder(self._clone_dir,
                            engine_config.get('extras', ()))
        context = builder.create_with_context(venv_path)

        self._python_executable = context.env_exe

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


class EnvBuilder(venv.EnvBuilder):
    """EnvBuilder that installs a project and any specified extras.
    """
    def __init__(self, repo_dir, extras, *args, **kwargs):
        super().__init__(self, with_pip=True, symlinks=True, *args, **kwargs)
        self.repo_dir = repo_dir

        self.extras = tuple(extras)

    def create_with_context(self, env_dir):
        # A bit if a hack. We remember the context seen in a call to
        # `post_setup()` and return it here.
        self._context = None

        super().create(env_dir)

        assert self._context is not None
        return self._context

    def post_setup(self, context):
        self._context = context

        command = '{} -m pip install -e .{}'.format(
            context.env_exe,
            '[{}]'.format(','.join(self.extras)) if self.extras else '')

        log.info('Running installation command: {}'.format(command))

        subprocess.run(command.split(),
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       cwd=self.repo_dir,
                       check=True)

