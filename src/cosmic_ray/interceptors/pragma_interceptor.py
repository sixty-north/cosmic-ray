from parso.tree import Node

from cosmic_ray.ast import get_node_pragma_categories
from cosmic_ray.interceptors.base import Interceptor
from cosmic_ray.operators.operator import Operator
from cosmic_ray.work_item import WorkItem, WorkResult, WorkerOutcome


class PragmaInterceptor(Interceptor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pragma_cache = None

    def pre_scan_module_path(self, module_path):
        self._pragma_cache = {}
        return True

    def post_add_work_item(self,
                           operator: Operator,
                           node: Node,
                           new_work_item: WorkItem):
        if self._have_excluding_pragma(node, operator):
            self._record_skipped_result_item(new_work_item.job_id)

    def _record_skipped_result_item(self, job_id):
        self.work_db.set_result(
            job_id,
            WorkResult(
                worker_outcome=WorkerOutcome.SKIPPED,
                output="Skipped: pragma found",
            )
        )

    def _have_excluding_pragma(self, node, operator: Operator) -> bool:
        """
        Return true if node have à pragma declaration that exclude
        self.operator. For this it's look for 'no mutation' pragma en analyse
        sub category of this pragma declaration.

        It use cache mechanism of pragma information across visitors.
        """

        pragma_categories = self._pragma_cache.get(node, True)
        # pragma_categories can be (None, False, list):
        #   use True as guard

        if pragma_categories is True:
            pragma = get_node_pragma_categories(node)
            if pragma:
                pragma_categories = pragma.get('no mutate', False)
            else:
                pragma_categories = False
            # pragma_categories is None: Exclude all operator
            # pragma_categories is list: Exclude operators in the list
            # pragma_categories is False:
            #    guard indicate no pragma: no filter
            self._pragma_cache[node] = pragma_categories

        if pragma_categories is False:
            return False

        if pragma_categories is None:
            return True

        return operator.pragma_category_name in pragma_categories
