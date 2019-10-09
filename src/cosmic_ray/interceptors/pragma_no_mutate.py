"""An interceptor that uses metadata: no mutate to determine when specific mutations
should be skipped.
"""
import re
from functools import lru_cache
import logging

from cosmic_ray.interceptors import Interceptor
from cosmic_ray.work_item import WorkerOutcome

log = logging.getLogger()


class PragmaNoMutateInterceptor(Interceptor):
    def post_init(self):
        """Mark lines with "# pragma: no mutate" as SKIPPED

        For all work_item in db, if the LAST line of the working zone is marked
         with "# pragma: no mutate", This work_item will be skipped.
        """

        @lru_cache()
        def file_contents(file_path):
            "A simple cache of file contents."
            with file_path.open(mode="rt") as handle:
                return handle.readlines()

        re_is_mutate = re.compile(r'.*#.*pragma:.*no mutate.*')

        for item in self.work_db.work_items:
            lines = file_contents(item.module_path)
            try:
                # item.{start,end}_pos[0] seems to be 1-based.
                line_number = item.end_pos[0] - 1
                if item.end_pos[1] == 0:
                    # The working zone ends at begin of line,
                    # consider the previous line.
                    line_number -= 1
                line = lines[line_number]
                if re_is_mutate.match(line):
                    self._add_work_result(
                        item,
                        output="Skipped by pragma no mutate",
                        worker_outcome=WorkerOutcome.SKIPPED,
                    )
            except Exception as ex:
                raise Exception("module_path: %s, start_pos: %s, end_pos: %s, len(lines): %s" %
                                (item.module_path, item.start_pos, item.end_pos, len(lines))) from ex
