"""Implementation of the mutating operator core.
"""

import ast
import logging

import cosmic_ray.util

log = logging.getLogger()


def _full_module_name(obj):
    return '{}.{}'.format(
        obj.__class__.__module__,
        obj.__class__.__name__)


class MutatingCore:
    """
    An `Operator` core which performs mutation of ASTs.

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

    def visit_mutation_site(self, node, op,  # pylint: disable=invalid-name
                            num_mutations):
        """Potentially mutate `node`, returning the mutated version.

        `Operator` calls this when AST iteration reaches a
        potential mutation site. If that site is scheduled for
        mutation, the subclass instance will be asked to perform the
        mutation.
        """
        # If the current operator will do at least that many mutations,
        # then let it make the mutation now.
        if self._count <= self._target < self._count + num_mutations:
            assert self._activation_record is None
            assert self._target - self._count < num_mutations

            self._activation_record = {
                'operator': _full_module_name(op),
                'occurrence': self._target,
                'line_number': cosmic_ray.util.get_line_number(node)
            }

            old_node = node
            node = op.mutate(old_node, self._target - self._count)
            # add lineno and col_offset for newly created nodes
            ast.fix_missing_locations(node)

        self._count += num_mutations
        return node

    def repr_args(self):
        "Extra arguments to display in operator reprs."
        return [('target', self._target)]
