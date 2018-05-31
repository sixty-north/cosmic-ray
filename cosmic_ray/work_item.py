"""A `WorkItem` carries information about potential and completed work in the
Cosmic Ray system.

`WorkItem` is one of the central structures in CR. It can describe both work
to be done and work that has been done, and it indicates how test sessions have
completed.
"""
import json
from collections import MutableMapping


class WorkItem(MutableMapping):
    """The details of a specific mutation and test run in Cosmic Ray.
    """

    FIELDS = [
        # Arbitrary data returned by the concrete TestRunner to provide more
        # information about the test results.
        'data',

        # A test_runner.TestOutcome from the test run.
        'test_outcome',

        # A worker.WorkOutcome describing how the worker completed.
        'worker_outcome',

        # The diff produced by the operators
        'diff',

        # the module to be mutated
        'module',

        # The name of the operator
        'operator',

        # The occurrence on which the operator was applied.
        'occurrence',

        # The name of the mutated source file
        'filename',

        # The line number at which the operator was applied.
        'line_number',

        # The column offset at which the operator was applied
        'col_offset',

        'command_line',

        'job_id'
    ]

    def __init__(self, vals=None, **kwargs):
        super().__setattr__('_dict', dict.fromkeys(WorkItem.FIELDS))
        values = vals or dict()
        kwargs.update(values)
        for key, value in kwargs.items():
            self[key] = value

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return iter(self._dict)

    def __contains__(self, name):
        return name in WorkItem.FIELDS

    def __getattr__(self, name):
        if name not in WorkItem.FIELDS:
            raise AttributeError('No attribute {!r} in {}'.format(name, self.__class__.__name__))
        return self._dict[name]

    def __setattr__(self, name, value):
        if name not in WorkItem.FIELDS:
            raise AttributeError('No attribute {!r} in {}'.format(name, self.__class__.__name__))
        self._dict[name] = value

    def __getitem__(self, name):
        if name not in WorkItem.FIELDS:
            raise KeyError('No field {!r} in {}'.format(name, self.__class__.__name__))
        return self._dict[name]

    def __setitem__(self, name, value):
        if name not in WorkItem.FIELDS:
            raise KeyError('No field {!r} in {}'.format(name, self.__class__.__name__))
        self._dict[name] = value

    def __delitem__(self, name):  # pylint: disable=unused-argument
        msg = '{} does not support deleting fields: {!r}'.format(self.__class__.__name__, name)
        raise KeyError(msg)

    def __getstate__(self):
        return self.as_dict()

    def __setstate__(self, state):
        # Avoids __setitem__
        super().__setattr__('_dict', dict())
        self._dict.update(state)

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            ', '.join("{key!s}={value!r}".format(key=name, value=self[name]) for name in self.FIELDS))

    def as_dict(self):
        return self._dict.copy()


class WorkItemJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, WorkItem):
            return {
                "_type": "WorkItem",
                "values": obj.as_dict()
            }
        return super().default(obj)


class WorkItemJsonDecoder(json.JSONDecoder):

    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook)

    def object_hook(self, obj):
        if ('_type' in obj) and (obj['_type'] == 'WorkItem') and ('values' in obj):
            values = obj['values']
            return WorkItem(vals=values)
        return obj
