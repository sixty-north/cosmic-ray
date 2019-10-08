from typing import Dict

import parso
import sys

from cosmic_ray.commands.init import visit_module
from cosmic_ray.config import ConfigDict
from cosmic_ray.interceptors import Interceptors
from cosmic_ray.interceptors.annotation_interceptor import \
    AnnotationInterceptor
from cosmic_ray.work_item import WorkResult, WorkItem


class Data:
    def __init__(self):
        self.results = {}  # type: Dict[str, WorkResult]
        self.work_items = {}  # type: Dict[str, WorkItem]

    def add_work_item(self, work_item: WorkItem):
        self.work_items[work_item.job_id] = work_item

    def set_result(self, job_id, work_result: WorkResult):
        self.results[job_id] = work_result

    @property
    def merged_results(self):
        results = ((w, self.results.get(job_id))
                   for job_id, w in self.work_items.items())

        return {
            (w.operator_name, w.occurrence):
                (w.start_pos, w.end_pos,
                 (r.test_outcome, r.worker_outcome) if r else (None, None))
            for w, r in results  # type: WorkItem, WorkResult
        }

    config = {'pragma': {'filter-no-coverage': True}}

    operator_names = [
        'core/ReplaceOrWithAnd',
        # 'core/StringReplacer',
    ]

    if sys.version_info < (3, 6):
        content = """
        a = 1 or 2
        def f(a: int or float) -> str or float:
            return a or True
        def f(a):
            a or False
        """

        expected = {
            ('core/ReplaceOrWithAnd', 0): ((2, 14), (2, 16), (None, None)),
            ('core/ReplaceOrWithAnd', 1): ((4, 21), (4, 23), (None, None)),
            ('core/ReplaceOrWithAnd', 2): ((6, 14), (6, 16), (None, None)),
        }

    else:
        content = """
        a: int or str = 1 or 2
        a = 1 or 2
        b: " annotation " = 2
        def f(a: int or float) -> str or float:
            return a or True
        def f(a):
            a or False
        """

        expected = {
            ('core/ReplaceOrWithAnd', 0): ((2, 26), (2, 28), (None, None)),
            ('core/ReplaceOrWithAnd', 1): ((3, 14), (3, 16), (None, None)),
            ('core/ReplaceOrWithAnd', 2): ((6, 21), (6, 23), (None, None)),
            ('core/ReplaceOrWithAnd', 3): ((8, 14), (8, 16), (None, None)),
        }


def test_interceptor():
    data = Data()
    interceptor = AnnotationInterceptor(data)

    visit_module(
        module_path="a.py",
        module_ast=parso.parse(data.content),
        work_db=data,
        interceptors=Interceptors([interceptor], data.config),
        operator_names=data.operator_names,
        config=ConfigDict(),
    )

    assert data.merged_results == data.expected
