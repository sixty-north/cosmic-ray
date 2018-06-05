"""JSON functions that work from python 3.4+.

Some parts of the standard json package aren't available on 3.4, so this smooths over the interface.
"""

import json


try:
    CatchType = json.JSONDecodeError
except AttributeError:
    CatchType = ValueError


class JSONDecodeError(ValueError):
    pass


def loads(*args, **kwargs):
    try:
        return json.loads(*args, **kwargs)
    except CatchType as exc:
        raise JSONDecodeError() from exc
