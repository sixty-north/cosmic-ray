from cosmic_ray.tools.filters import operators_filter
from cosmic_ray.work_item import WorkItem, WorkResult, WorkerOutcome


class Data:

    def __init__(self):
        self.count = 0
        self.results = []

    def new_work_item(self, operator_name, job_id):
        self.count += 1
        return WorkItem(
            module_path="{}.py".format(self.count),
            operator_name=operator_name,
            occurrence=self.count,
            start_pos=(self.count, self.count),
            end_pos=(self.count+1, self.count+1),
            job_id=job_id,
        )

    @property
    def pending_work_items(self):
        return [
            self.new_work_item("Op1", "id1"),
            self.new_work_item("Op2", "id2"),
            self.new_work_item("Op3", "id3"),
            self.new_work_item("Op2", "id4"),
            self.new_work_item("Opregex1", "regex1"),
            self.new_work_item("Opregex2", "regex2"),
            self.new_work_item("Opregex3", "regex3"),
            self.new_work_item("Complex1", "regex4"),
            self.new_work_item("CompLex2", "regex5"),
        ]

    def set_result(self, job_id, work_result: WorkResult):
        self.results.append((job_id, work_result.worker_outcome))

    @property
    def expected_after_filter(self):
        return [
            ("id1", WorkerOutcome.SKIPPED),
            ("id2", WorkerOutcome.SKIPPED),
            ("id4", WorkerOutcome.SKIPPED),
            ("regex1", WorkerOutcome.SKIPPED),
            ("regex2", WorkerOutcome.SKIPPED),
            ("regex4", WorkerOutcome.SKIPPED),
        ]

    @property
    def expected_all_filtered(self):
        return [
            ("id1", WorkerOutcome.SKIPPED),
            ("id2", WorkerOutcome.SKIPPED),
            ("id3", WorkerOutcome.SKIPPED),
            ("id4", WorkerOutcome.SKIPPED),
            ("regex1", WorkerOutcome.SKIPPED),
            ("regex2", WorkerOutcome.SKIPPED),
            ("regex3", WorkerOutcome.SKIPPED),
            ("regex4", WorkerOutcome.SKIPPED),
            ("regex5", WorkerOutcome.SKIPPED),
        ]


def test_operators_filter():
    data = Data()
    exclude = [
        'Op1', 'Op2', 'Opregex[12]', r'(?:.[oO]m(?:p|P)lex).*'
    ]
    operators_filter.OperatorsFilter()._skip_filtered(data, exclude)
    assert data.results == data.expected_after_filter


def test_operators_filter_empty_excludes():
    data = Data()
    exclude = []
    operators_filter.OperatorsFilter()._skip_filtered(data, exclude)
    assert data.results == []


def test_operators_filter_all_excluded():
    data = Data()
    exclude = [r"."]
    operators_filter.OperatorsFilter()._skip_filtered(data, exclude)
    assert data.results == data.expected_all_filtered
