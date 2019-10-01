"Implementation of operator base class."
import re
from abc import ABC, abstractmethod


_re_camel_to_kebab_case = re.compile(r'([a-z0-9])([A-Z])')


class Operator(ABC):
    """The mutation operator base class.

    Args:
        python_version: The version of Python to use when interpreting the code in `module_path`.
            A string of the form "MAJOR.MINOR", e.g. "3.6" for Python 3.6.x.
    """

    def __init__(self, python_version):
        self._python_version = python_version
        self._pragma_category_name = None

    @property
    def python_version(self):
        "Python major.minor version as a string."
        return self._python_version

    @property
    def pragma_category_name(self):
        if self._pragma_category_name is None:
            name = type(self).__name__
            # Removing remove because this is a pragma category name after: 'no mutate'
            if name.startswith('Remove'):
                name = name[len('Remove'):]
            name = _re_camel_to_kebab_case.sub(r'\1-\2', name).lower()
            self._pragma_category_name = name

        return self._pragma_category_name

    @abstractmethod
    def mutation_positions(self, node):
        """All positions where this operator can mutate `node`.

        An operator might be able to mutate a node in multiple ways, and this
        function should produce a position description for each of these
        mutations. Critically, if an operator can make multiple mutations to the
        same position, this should produce a position for each of these
        mutations (i.e. multiple identical positions).

        Returns: An iterable of `((start-line, start-col), (stop-line,
            stop-col))` tuples describing the locations where this operator will
            mutate `node`
        """

    @abstractmethod
    def mutate(self, node, index):
        """Mutate a node in an operator-specific manner.

        Return the new, mutated node. Return `None` if the node has
        been deleted. Return `node` if there is no mutation at all for
        some reason.
        """

    @classmethod
    @abstractmethod
    def examples(cls):
        """Examples of the mutations that this operator can make.

        This is primarily for testing purposes, but it could also be used for
        documentation.

        Each example is a tuple of the form `(from-code, to-code, index)`. The
        `index` is optional and will be assumed to be 0 if it's not included.
        The `from-code` is a string containing some Python code prior to
        mutation. The `to-code` is a string describing the code after mutation.
        `index` indicates the occurrence of the application of the operator to
        the code (i.e. for when an operator can perform multiple mutation to a
        piece of code).

        Returns: An iterable of example tuples.
        """
