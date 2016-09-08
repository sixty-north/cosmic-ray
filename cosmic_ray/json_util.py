"""Utilities for working with JSON data.

This is where we provide support for JSON en/decoding of any special types we
have.
"""

import json

from .testing.test_runner import Outcome


class JSONEncoder(json.JSONEncoder):

    """
    A JSON encoder that knows how to encode any specific types we need.

    To use this, pass it as the `cls` argument to `json.dumps`:

        obj = . . . some structure with a DataFrame in it . . .
        encoded_obj = json.dumps(obj, cls=DataFrameJSONEncoder)
    """

    def default(self, obj):
        if isinstance(obj, Outcome):
            return str(obj)
        return json.JSONEncoder.default(self, obj)
