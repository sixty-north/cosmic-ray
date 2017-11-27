"""Functions related to finding modules for testing."""

import importlib
import logging
import os
import pkgutil
import re

log = logging.getLogger()


def fixup_module_name(name):
    """If `name` appears to be a source file name, this converts it to a module
    name. Otherwise this returns `name` inchanged.

    For example, if you pass in "foo/bar.py", this will return "foo.bar". If
    you pass in "llama.yak", this just returns "llama.yak".

    This is primarily a convenience function to allow users to use
    bash-completion when specifying module names.
    """
    if os.path.exists(name):
        if name.endswith('.py'):
            name = name[:-3]
        name = name.replace('/', '.')
    return name


def find_modules(name, excludes=None):
    """Generate sequence of all submodules of NAME, including NAME itself.

    `excludes` is a sequence of regular expression. If a full module name
    matches any of these expressions then it won't be returned in the results.
    Critically, no module beneath an excluded module will be reported either.

    Given a directory structure like this:

        /a/
          __init__.py
          b.py
          c/
              __init__.py
              d.py

    you get this:

        >>> list(find_modules('a'))
        [<module 'a' from 'a/__init__.py'>,
         <module 'a.b' from 'a/b.py'>,
         <module 'a.c' from 'a/c/__init__.py'>,
         <module 'a.c.d' from 'a/c/d.py'>]

    """
    excludes = excludes or []
    module_names = [name]
    exclude_patterns = [re.compile(ex) for ex in excludes]
    while module_names:
        module_name = module_names.pop()
        try:

            if any([pattern.match(module_name)
                    for pattern in exclude_patterns]):
                continue

            module = importlib.import_module(module_name)

            yield module

            if hasattr(module, '__path__'):
                for _, _name, _ in pkgutil.iter_modules(module.__path__):
                    module_names.append(
                        '{}.{}'.format(module_name, _name))
        except Exception:  # pylint:disable=broad-except
            log.exception(
                'Unable to import %s',
                module_name)
