def make_record(name, fields=(), docstring=""):
    """Create a new record class.

    A Record is fundamentally a dict with a specified set of keys. These keys
    will always have a value (defaulting to None), they can't be removed, and
    new keys can not be added.

    This may sound a lot like a class, and that's true. The main benefit of
    records is that they can be treated directly like dicts for the most part,
    and, critically, they are easy to JSON-ify. Also, like classes, they ensure
    that they're only used in the correct way, i.e. users can only access the
    specified fields. This prevents the confusion of using simple dicts where
    people can use conflicting or confusing key names.

    Args:
        name: The name of the class to be created.
        fields: The names of the fields in the record.
        docstring: The docstring for the record class.

    Returns: A new class derived from dict with the specified fields.

    """

    def __init__(self, vals=None, **kwargs):
        dict.__init__(self, dict.fromkeys(fields))
        values = vals or dict()
        kwargs.update(values)
        for key, value in kwargs.items():
            self[key] = value

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError('no attribute {}'.format(name))

    def __setattr__(self, name, value):
        try:
            self[name] = value
        except KeyError:
            raise AttributeError('no attribute {}'.format(name))

    def __getitem__(self, name):
        if name not in self:
            raise KeyError('no field {} in record'.format(name))
        return dict.__getitem__(self, name)

    def __setitem__(self, name, value):
        if name not in self:
            raise KeyError('no field {} in record'.format(name))
        dict.__setitem__(self, name, value)

    def __delitem__(self, name):  # pylint: disable=unused-argument
        msg = 'record does not support deleting fields: {}'.format(name)
        raise KeyError(msg)

    def update(self, container):
        for key, values in container.items():
            self[key] = values

    attrs = {
        '__init__': __init__,
        '__getattr__': __getattr__,
        '__setattr__': __setattr__,
        '__getitem__': __getitem__,
        '__setitem__': __setitem__,
        '__delitem__': __delitem__,
        'update': update
    }

    rec = type(name, (dict,), attrs)
    rec.__doc__ = docstring
    return rec


WorkRecord = make_record(  # pylint: disable=invalid-name
    'WorkRecord',

    [
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

        # The name of the operators
        'operator',

        # The occurrence on which the operator was applied.
        'occurrence',

        # The line number at which the operator was applied.
        'line_number',

        'command_line',
        'job_id'
    ],
    docstring=" The details of a specific mutation and test run in CosmicRay."
)
