import importlib
import pkgutil


def find_modules(name):
    """Generate the paths to all submodules of the module named NAME.

    Given a directory structure like this:

        /a/
          __init__.py
          b.py
          c/
              __init__.py
              d.py

    you get this:

        >>> list(find_modules('a'))
        ['/a/__init__.py',
         '/a/b.py',
         '/a/c/__init__.py',
         '/a/c/d.py']
    """
    module_names = [name]
    while module_names:
        module_name = module_names.pop()
        print('importing', module_name)
        module = importlib.import_module(module_name)

        yield module.__file__

        if hasattr(module, '__path__'):
            for loader, name, ispkg in pkgutil.iter_modules(module.__path__):
                module_names.append(
                    '{}.{}'.format(
                        module_name, name))
