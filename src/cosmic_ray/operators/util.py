"Utilities for implementing operators."


def extend_name(suffix):
    """A factory for class decorators that modify the class name by appending some text to it.

    Example:

    .. code-block:: python

        @extend_name('_Foo')
        class Class:
            pass

        assert Class.__name__ == 'Class_Foo'
    """

    def dec(cls):
        name = "{}{}".format(cls.__name__, suffix)
        setattr(cls, "__name__", name)
        return cls

    return dec
