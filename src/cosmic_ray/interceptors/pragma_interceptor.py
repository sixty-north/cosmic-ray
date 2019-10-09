import re
from functools import lru_cache
from typing import Dict, List

from parso.tree import Node

from cosmic_ray.ast import get_comment_on_node_line
from cosmic_ray.interceptors.base import Interceptor
from cosmic_ray.operators.operator import Operator
from cosmic_ray.util import to_kebab_case
from cosmic_ray.work_item import WorkItem, WorkerOutcome


class PragmaInterceptor(Interceptor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_no_coverage = False
        self._cache_pragma = None

    def set_config(self, config):
        self.filter_no_coverage = config.get('filter-no-coverage', False)

    def pre_scan_module_path(self, module_path):
        self._cache_pragma = {}
        return True

    def post_add_work_item(self,
                           operator: Operator,
                           node: Node,
                           work_item: WorkItem):
        if self._have_excluding_pragma(node, operator):
            self._add_work_result(
                work_item,
                worker_outcome=WorkerOutcome.SKIPPED,
                output="Skipped: pragma found",
            )

    def _have_excluding_pragma(self, node, operator: Operator) -> bool:
        """
        Return true if node have à pragma declaration that exclude
        self.operator. For this it's look for 'no mutation' pragma en analyse
        sub category of this pragma declaration.

        It use cache mechanism of pragma information across visitors.
        """

        pragma_categories = self._cache_pragma.get(node)

        if pragma_categories is None:
            pragma = get_node_pragma_categories(node)
            if pragma:
                pragma_categories = pragma.get('no mutate')
                if self.filter_no_coverage:
                    no_coverage = pragma.get('no coverage')
                    if no_coverage:
                        pragma_categories = True
            else:
                pragma_categories = False
            # pragma_categories is True: Exclude all operator
            # pragma_categories is list: Exclude operators in the list
            self._cache_pragma[node] = pragma_categories

        if isinstance(pragma_categories, bool):
            return pragma_categories

        category_name = self._get_operator_pragma_category_name(operator)
        return category_name in pragma_categories

    @staticmethod
    @lru_cache()
    def _get_operator_pragma_category_name(operator):
        name = getattr(operator, 'pragma_category_name', None)
        if not name:
            name = type(operator).__name__
            # Removing 'Remove' because this is a pragma category name after: 'no mutate'
            if name.startswith('Remove'):
                name = name[len('Remove'):]
            name = to_kebab_case(name)
        return name


def get_node_pragma_categories(node) -> None or Dict[str, bool or List[str]]:
    """
    Get pragma dictionary `see get_pragma_list` declared on the line
    of the node
    """
    comment = get_comment_on_node_line(node)
    if comment:
        return get_pragma_list(comment)
    else:
        return None


_re_pragma = re.compile(r'([-A-Za-z0-9](?: (?! )|[-A-Za-z0-9])*)(:?)(,?)')


def get_pragma_list(line: str) -> None or Dict[str, bool or List[str]]:
    """
    Pragma syntax:
    - Any comment can be present before 'pragma:' declaration
    - You can have multiple pragma family separated with double space
        (allowing family name having multiple words)
    - You can declare sections of pragma if the pragma name is followed
        directly with ':'
    - Pragma family can have an empty section set if no section is declared
        after ':'  ex "fam:" or "fam1:  fam2
    - Section names can have a space (two spaces indicate the end
        of section list)
    - Sections are separated with ',', comma directly present after the
        previous section (no space)

    :return Dictionary of list of sections per pragma family.
        If a pragma family have no section, the dictionary will returns True

    >>> get_pragma_list("# comment")
    None
    >>> get_pragma_list("# comment pragma:")
    {}
    >>> get_pragma_list("# comment pragma: x y  z")
    {'x y': True, 'z': True}
    >>> get_pragma_list("# comment pragma: x:")
    {'x': []}
    >>> get_pragma_list("# comment pragma: x:  y")
    {'x': [], 'y': True}
    >>> get_pragma_list("# comment pragma: x y  z: d, e")
    {'x y': True, 'z': ['d', 'e']}
    >>> get_pragma_list("# comment pragma: x: a, b, c  y z: d, e")
    {'x': ['a', 'b', 'c'], 'y z': ['d', 'e']}
    >>> get_pragma_list("comment pragma: x: a, b, c y  z: d, e")
    {'x': ['a', 'b', 'c y'], 'z': ['d', 'e']}
    """
    split = line.split('pragma:', maxsplit=1)
    if len(split) == 1:
        return None
    pragma_list = split[1]

    pragma = {}
    family_name = None
    last_section_pos = None
    for m in _re_pragma.finditer(pragma_list):
        elt = m.group(1)

        if family_name and m.start() > last_section_pos + 1:
            # The element is too far away, a new family is starting
            family_name = None

        if family_name:
            # If family_name in progress, add elt as section
            pragma[family_name].append(elt)
            if not m.group(3):
                # If no comma, next will be a key
                family_name = None
                last_section_pos = None
            else:
                last_section_pos = m.end()
        else:
            # No family_name in progress, elt is the family_name
            if m.group(2):
                # Followed by ':', next will be a section
                family_name = elt
                pragma[family_name] = []
                last_section_pos = m.end()
            else:
                # No ':', this family_name have no section,
                # next is another family_name
                pragma[elt] = True
    return pragma
