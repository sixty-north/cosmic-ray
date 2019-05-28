=======
Cloning
=======

TODO: Document Cloning

When Cosmic Ray mutates code, it generally does so on a copy of the original
source code. Since Cosmic Ray mutates code directly on disk, it needs to make
copies of the code in order to safely run concurrent tests.

Cosmic Ray supports several methods for copying code, including simple file system copies
as well as git cloning. These methods are currently hard-coded, but we'll probably provide cloning
methods via plugins at some point.

You can configure cloning in your configuration TOML in the
`cosmic-ray.cloning` section. At a minimum, you must have a
`cosmic-ray.cloning.method` entry in your config.

The "copy" cloning method simple copies an entire filesystem directory tree. You can use configure it like
this::

    [cosmic-ray.cloning]
    method = 'copy'
    commands = []

The "git" method clones a git repository to make a clone. You can configure it like this::

    [cosmic-ray.cloning]
    method = 'git'
    repo-uri = "https://github.com/project/repo.git"  # Or "." to clone the local repo
    commands = [
        "pip install .[test]"
    ]

Commands
========

The `commands` entry is a list of shell commands that will be executed in order
after the copy/clone has been created. They commands will be executed from the
root of the clone and with the new virtual environment activated. You almost
always need to execute at least one command to install your package, e.g.
``python setup.py install``.
