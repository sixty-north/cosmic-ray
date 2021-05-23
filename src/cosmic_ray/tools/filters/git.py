"""A filter that uses git to determine when specific files/lines
should be skipped.
"""
import logging
import re
import subprocess
import sys
from argparse import Namespace
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from cosmic_ray.config import ConfigDict, load_config
from cosmic_ray.work_db import WorkDB
from cosmic_ray.work_item import WorkerOutcome, WorkResult
from cosmic_ray.tools.filters.filter_app import FilterApp

log = logging.getLogger()


class GitFilter(FilterApp):
    """Implements the git filter."""

    def description(self):
        return __doc__

    def _git_news(self, branch):
        """Get the set of new lines by file"""
        # we could use interlap, but do not want to
        # add new dependency at the moment
        diff = subprocess.run(["git", "diff", "--relative", "-U0", branch, "."], capture_output=True)
        regex = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@.*")
        current_file = None
        res = defaultdict(set)
        for diff_line in diff.stdout.decode("utf-8").split("\n"):
            if diff_line.startswith("@@"):
                m = regex.match(diff_line)
                start = int(m.group(1))
                lenght = int(m.group(2)) if m.group(2) is not None else 1
                for line in range(start, start + lenght):
                    res[current_file].add(line)
            if diff_line.startswith("+++ b/"):
                current_file = Path(diff_line[6:])
        return res

    def _skip_filtered(self, work_db, branch):
        git_news = self._git_news(branch)

        for item in work_db.pending_work_items:
            for mutation in item.mutations:
                if mutation.module_path not in git_news or not (
                    git_news[mutation.module_path] & set(range(mutation.start_pos[0], mutation.end_pos[0] + 1))
                ):
                    log.info(
                        "git skipping %s %s %s %s %s %s",
                        item.job_id,
                        mutation.operator_name,
                        mutation.occurrence,
                        mutation.module_path,
                        mutation.start_pos,
                        mutation.end_pos,
                    )

                    work_db.set_result(
                        item.job_id,
                        WorkResult(
                            output="Filtered git",
                            worker_outcome=WorkerOutcome.SKIPPED,
                        ),
                    )

    def filter(self, work_db: WorkDB, args: Namespace):
        """Mark as skipped all work item that is not new"""

        config = ConfigDict()
        if args.config is not None:
            config = load_config(args.config)

        branch = config.sub("git", "git-filter").get("branch", "master")
        self._skip_filtered(work_db, branch)

    def add_args(self, parser):
        parser.add_argument("--config", help="Config file to use")


def main(argv=None):
    """Run the operators-filter with the specified command line arguments."""
    return GitFilter().main(argv)


if __name__ == "__main__":
    sys.exit(main())