import ast
import collections
import copy
import itertools
import logging

import cosmic_ray.util


LOG = logging.getLogger()


MutationRecord = collections.namedtuple('MutationRecord',
                                        ['module_name',
                                         'module_file',
                                         'operator',
                                         'activation_record',
                                         'mutant'])


def _full_module_name(obj):
    return '{}.{}'.format(
        obj.__class__.__module__,
        obj.__class__.__name__)


class MutatingCore:
    """An `Operator` core which performs mutation of ASTs.

    This core is instantiated with a target count N. The Nth time the operator
    using the core calls `visit_mutation_site()`, this core will set the
    `activation_record` attribute and perform a mutation. In other words, this
    will mutate the `target`-th instance of an operator's mutation candidates
    if such a candidate exists. If there is no `target`-th candidate then
    `activation_record` will remain `None` and no mutation will occur.

    """
    def __init__(self, target):
        self._target = target
        self._count = 0
        self._activation_record = None

    @property
    def activation_record(self):
        """The activation record for the operator.

        The activation record is a dict describing where and how the
        operator was applied.
        """
        return self._activation_record

    def visit_mutation_site(self, node, op):
        """Potentially mutate `node`, returning the mutated version.

        `Operator` calls this when AST iteration reaches a
        potential mutation site. If that site is scheduled for
        mutation, the subclass instance will be asked to perform the
        mutation.
        """
        if self._count == self._target:
            self._activation_record = {
                'operator': _full_module_name(self),
                'description': str(self),
                'line_number': cosmic_ray.util.get_line_number(node)
            }

            old_node = node
            node = op.mutate(old_node)
            ast.copy_location(node, old_node)

        self._count += 1
        return node

    def repr_args(self):
        return [('target', self._target)]
