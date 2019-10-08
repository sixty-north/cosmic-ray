from cosmic_ray.interceptors.operators_filter import OperatorsFilterInterceptor
from cosmic_ray.work_item import WorkItem, WorkResult, WorkerOutcome


class Data:
    count = 0
    results = []

    config = {'exclude-operators': [
        'Op1','Op2', 'Opregex[12]', r'(?:.[oO]m(?:p|P)lex).*'
    ]}

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
    def expected(self):
        return [
            ("id1", WorkerOutcome.SKIPPED),
            ("id2", WorkerOutcome.SKIPPED),
            ("id4", WorkerOutcome.SKIPPED),
            ("regex1", WorkerOutcome.SKIPPED),
            ("regex2", WorkerOutcome.SKIPPED),
            ("regex4", WorkerOutcome.SKIPPED),
        ]


def test_operators_filter():
    data = Data()
    interceptor = OperatorsFilterInterceptor(data)
    interceptor.set_config(data.config)
    interceptor.post_init()
    assert data.results == data.expected
