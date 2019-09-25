"""An interceptor that uses metadata: no mutate to determine when specific mutations
should be skipped.
"""
import re
from functools import lru_cache
import logging

from cosmic_ray.work_item import WorkerOutcome, WorkResult

log = logging.getLogger()


def intercept(work_db):
    """Look for WorkItems in `work_db` that should not be mutated due to spor metadata.

    For each WorkItem, find anchors for the item's file/line/columns. If an
    anchor exists with metadata containing `{mutate: False}` then the WorkItem
    is marked as SKIPPED.
    """

    @lru_cache()
    def file_contents(file_path):
        "A simple cache of file contents."
        with file_path.open(mode="rt") as handle:
            return handle.readlines()

    re_is_mutate = re.compile(r'.*#.*pragma:.*no mutate.*')

    for item in work_db.work_items:
        lines = file_contents(item.module_path)
        try:
            line_number = item.end_pos[0] - 1
            if item.end_pos[1] == 0:
                line_number -= 1
            line = lines[line_number]
            if re_is_mutate.match(line):
                work_db.set_result(item.job_id,
                                   WorkResult(output=None,
                                              test_outcome=None,
                                              diff=None,
                                              worker_outcome=WorkerOutcome.SKIPPED))
        except Exception as ex:
            raise Exception("module_path: %s, start_pos: %s, end_pos: %s, len(lines): %s" %
                            (item.module_path, item.start_pos, item.end_pos, len(lines))) from ex
