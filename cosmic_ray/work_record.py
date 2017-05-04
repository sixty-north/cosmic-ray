def make_record(name, *fields):
    def __init__(self, vals=None, **kwargs):
        dict.__init__(self, dict.fromkeys(fields))
        vals = vals or dict()
        kwargs.update(vals)
        for k, v in kwargs.items():
            self[k] = v

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

    def __delitem__(self, name):
        raise KeyError('record does not support deleting fields: {}'.format(name))

    def update(self, d):
        for k, v in d.items():
            self[k] = v

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
    return rec


WorkRecord = make_record(
    'WorkRecord',

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
)
