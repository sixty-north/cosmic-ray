"""A filter that skips mutations outside configured line ranges."""

import logging
import sys
from argparse import Namespace

from collections.abc import Mapping
from pathlib import Path

from cosmic_ray.config import ConfigDict, load_config
from cosmic_ray.tools.filters.filter_app import FilterApp
from cosmic_ray.work_db import WorkDB
from cosmic_ray.work_item import WorkResult, WorkerOutcome

log = logging.getLogger()


class LineFilter(FilterApp):
    """Implements the line filter."""

    def description(self):
        return __doc__

    def add_args(self, parser):
        parser.add_argument("--config", help="Config file to use")

    def filter(self, work_db: WorkDB, args: Namespace):
        config = ConfigDict()
        if args.config is not None:
            config = load_config(args.config)

        module_path = config.get("module-path", "")

        if isinstance(module_path, list):
            if len(module_path) != 1:
                raise ValueError(
                    "line-filter does not support multiple 'module-path' entries; "
                    "configure a single module-path when using this filter."
                )
            module_path = module_path[0]

        lf_config = config.sub("filters", "line-filter")
        raw_lines_cfg = lf_config.get("lines")

        normalized_lines_cfg = self._normalize_lines_config(raw_lines_cfg)
        line_ranges = self._parse_line_files(normalized_lines_cfg, module_path)

        if not line_ranges:
            log.warning(
                "line-filter: no line ranges configured; all mutations will be skipped",
            )

        log.info("Line filter included ranges: %s", line_ranges)

        self._skip_filtered(work_db, line_ranges)

    def _normalize_lines_config(self, lines_cfg):
        if lines_cfg is None:
            lines_cfg = {}
        if not isinstance(lines_cfg, Mapping):
            raise ValueError(
                "line-filter 'lines' section must be a mapping "
                "from module path to line specification(s)."
            )
            
        normalized_lines_cfg = {}
        for file_key, specs in lines_cfg.items():
            if isinstance(specs, str):
                specs_list = [specs]
            elif isinstance(specs, (list, tuple)):
                specs_list = list(specs)
            else:
                raise ValueError(
                    "line-filter 'lines' values must be a string or a list/tuple "
                    "of strings; got %r for %r" % (type(specs).__name__, file_key)
                )

            for spec in specs_list:
                if not isinstance(spec, str):
                    raise ValueError(
                        "line-filter 'lines' entries must be strings; got %r in %r" % (
                            type(spec).__name__,
                            file_key,
                        )
                    )

            normalized_lines_cfg[file_key] = specs_list
        return normalized_lines_cfg


    def _resolve_module_path(self, file_key, module_path_cfg):
        base = Path(module_path_cfg) if module_path_cfg else None
        file_path = Path(file_key)

        if not file_path.is_absolute() and base is not None:
            file_path = base / file_path

        return file_path

    def _parse_line_files(self, files, module_path_cfg):
        parsed = {}

        for file_key, specs in files.items():
            file_path = self._resolve_module_path(file_key, module_path_cfg)
            parsed[file_path] = self._parse_line_specs(specs)

        return parsed

    def _parse_line_specs(self, specs):
        ranges = []

        for spec in specs:
            spec = spec.strip()
            if not spec:
                continue

            try:
                if "-" in spec:
                    start, end = map(int, spec.split("-", 1))
                else:
                    start = end = int(spec)
            except ValueError:
                log.warning("line-filter: invalid line specification '%s' – skipping", spec)
                continue

            if start < 1 or end < start:
                log.warning(
                    "line-filter: nonsensical line range '%s' (interpreted as %s-%s) – skipping",
                    spec,
                    start,
                    end,
                )
                continue

            ranges.append((start, end))

        return ranges

    def _skip_filtered(self, work_db, parsed_files):
        job_ids = []

        for item in work_db.pending_work_items:
            for mutation in item.mutations:
                ranges = parsed_files.get(mutation.module_path)

                if not ranges or not self._ranges_overlap(
                    mutation.start_pos[0], mutation.end_pos[0], ranges
                ):
                    log.info(
                        "line-filter skipping %s %s %s %s %s %s",
                        item.job_id,
                        mutation.operator_name,
                        mutation.occurrence,
                        mutation.module_path,
                        mutation.start_pos,
                        mutation.end_pos,
                    )

                    job_ids.append(item.job_id)

        if job_ids:
            work_db.set_multiple_results(
                job_ids,
                WorkResult(
                    output="Filtered line-filter",
                    worker_outcome=WorkerOutcome.SKIPPED,
                ),
            )


    def _ranges_overlap(self, m_start, m_end, ranges):
        return any(m_start <= r_end and r_start <= m_end for r_start, r_end in ranges)


def main(argv=None):
    """Run the line-filter with the specified command line arguments."""
    return LineFilter().main(argv)


if __name__ == "__main__":
    sys.exit(main())
