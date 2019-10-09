class ASTQuery:
    """
    Allowing to navigate into any object and test attribute of any object:

    Examples:
    >>> ASTQuery(node).parent.match(Node, type='node').ok

    Test if node.parent isinstance of Node and node.parent.type == 'node'
    At each step (each '.' (dot)) you receive an ObjTest object, then

    Navigation:
    You can call any properties or functions of the base object
    >>> ASTQuery(node).parent.children[2].get_next_sibling()

    Test:
    >>> ASTQuery(node).match(attr='value').match(Class)
    All in once:
    >>> ASTQuery(node).match(Class, attr='value')

    Conditional navigation:
    >>> ASTQuery(node).IF.match(attr='intermediate').parent.FI

    Final result:
    >>> ASTQuery(node).ok
    >>> bool(ASTQuery(node))

    """
    def __init__(self, obj):
        self.obj = obj

    def _clone(self, obj) -> 'ASTQuery':
        return type(self)(obj)

    def match(self, clazz=None, **kwargs) -> 'ASTQuery':
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

    def __getattr__(self, item) -> 'ASTQuery':
        obj = self.obj
        if obj is None:
            return self
        return self._clone(getattr(obj, item))

    @property
    def IF(self):
        return ASTQueryOptional(self.obj, obj_test=self)

    def __call__(self, *args, **kwargs) -> 'ASTQuery':
        if self.obj is None:
            return self
        return self._clone(self.obj(*args, **kwargs))

    def __getitem__(self, item) -> 'ASTQuery':
        if self.obj is None:
            return self
        return self._clone(self.obj[item])


class ASTQueryOptional(ASTQuery):
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
