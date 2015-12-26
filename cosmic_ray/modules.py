import importlib
import logging
import pkgutil
import re

LOG = logging.getLogger()


def find_modules(name):
    """Generate sequence of all submodules of NAME, including NAME itself.

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
    module_names = [name]
    while module_names:
        module_name = module_names.pop()
        try:
            module = importlib.import_module(module_name)

            yield module

            if hasattr(module, '__path__'):
                for _, name, _ in pkgutil.iter_modules(module.__path__):
                    module_names.append(
                        '{}.{}'.format(
                            module_name, name))
        except Exception:  # pylint:disable=broad-except
            LOG.exception(
                'Unable to import %s',
                module_name)


def filtered_modules(modules, excludes):
    """Get the sequence of modules in `modules` which aren't filtered out
    by a regex in `excludes`.

    """
    exclude_patterns = [re.compile(ex) for ex in excludes]
    for module in modules:
        if not any([pattern.match(module.__name__)
                    for pattern in exclude_patterns]):
            yield module
