import logging
import os
import re

LOG = logging.getLogger()


def get_num_testers(num_testers, default=4):
    """Determine the number of testers to use.

    If `num_testers` is None, this returns `default`. If it's less
    than 1, this returns `os.cpu_count()`. Otherwise it returns
    `num_testers`. In all cases the return value will be integeral.
    """
    if num_testers < 1:
        num_testers = os.cpu_count()
    if num_testers is None:
        num_testers = default
    return int(num_testers)


def filtered_modules(modules, excludes):
    """Get the sequence of modules in `modules` which aren't filtered out
    by a regex in `excludes`.

    """
    exclude_patterns = [re.compile(ex) for ex in excludes]
    for module in modules:
        if not any([pattern.match(module.__name__)
                    for pattern in exclude_patterns]):
            yield module
