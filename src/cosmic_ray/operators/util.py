"Utilities for implementing operators."


def extend_name(suffix):
    """A factory for class decorators that modify the class name by appending some text to it.

    Example:

        @extend_name('_Foo')
        class Class:
            pass

        assert Class.__name__ == 'Class_Foo'
    """

    def dec(cls):
        name = '{}{}'.format(cls.__name__, suffix)
        setattr(cls, '__name__', name)
        return cls

    return dec


def dump_node(node, stdout=None):
    import sys
    stdout = stdout or sys.stdout
    write = stdout.write

    def do_dump(node, indent=''):
        write(f"{indent}{type(node).__name__}({node.type}")
        value = getattr(node, 'value', None)
        if value:
            value = value.replace('\n', '\\n')
            write(f", '{value}'")
        children = getattr(node, 'children', None)
        if children:
            write(', [\n')
            for child in children:
                do_dump(child, indent+' '*4)
                write(',\n')
            write(f"{indent}]")
        write(')')
        if not indent:
            write('\n')

    do_dump(node)


class ObjTest:
    """
    Allowing to navigate into any object and test attribute of any object:

    Examples:
    >>> ObjTest(node).parent.match(Node, type='node').ok

    Test if node.parent isinstance of Node and node.parent.type == 'node'
    At each step (each '.' (dot)) you receive an ObjTest object, then

    Navigation:
    You can call any properties or functions of the base object
    >>> ObjTest(node).parent.children[2].get_next_sibling()

    Test:
    >>> ObjTest(node).match(attr='value').match(Class)
    All in once:
    >>> ObjTest(node).match(Class, attr='value')

    Conditional navigation:
    >>> ObjTest(node).IF.match(attr='intermediate').parent.FI

    Final result:
    >>> ObjTest(node).ok
    >>> bool(ObjTest(node))

    """
    def __init__(self, obj):
        self.obj = obj

    def _clone(self, obj) -> 'ObjTest':
        return type(self)(obj)

    def match(self, clazz=None, **kwargs) -> 'ObjTest':
        obj = self.obj
        if obj is None:
            return self

        if clazz is None or isinstance(obj, clazz):
            for k, v in kwargs.items():
                op = None
                k__op = k.split('__')
                if len(k__op) == 2:
                    k, op = k__op
                node_value = getattr(obj, k)
                if op is None:
                    if node_value != v:
                        break
                elif op == 'in':
                    if node_value not in v:
                        break
                else:
                    raise ValueError("Can't handle operator %s", op)
            else:
                # All is true, continue recursion
                return self

        # A test fails
        return self._clone(None)

    @property
    def ok(self):
        return bool(self.obj)

    def __bool__(self):
        return self.ok

    def __getattr__(self, item) -> 'ObjTest':
        obj = self.obj
        if obj is None:
            return self
        return self._clone(getattr(obj, item))

    @property
    def IF(self):
        return ObjTestOptionnal(self.obj, obj_test=self)

    def __call__(self, *args, **kwargs) -> 'ObjTest':
        if self.obj is None:
            return self
        return self._clone(self.obj(*args, **kwargs))

    def __getitem__(self, item) -> 'ObjTest':
        if self.obj is None:
            return self
        return self._clone(self.obj[item])


class ObjTestOptionnal(ObjTest):
    def __init__(self, obj, obj_test=None):
        super().__init__(obj)
        self._initial = obj_test

    def _clone(self, obj):
        o = super()._clone(obj)
        o._initial = self._initial
        return o

    @property
    def FI(self):
        if self:
            return self._initial._clone(self.obj)
        else:
            return self._initial
