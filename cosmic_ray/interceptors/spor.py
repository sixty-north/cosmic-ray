"""An interceptor that uses spor metadata to determine when specific mutations
should be skipped.
"""
import logging

from spor.repo import find_anchors

from cosmic_ray.worker import WorkerOutcome

log = logging.getLogger()


def intercept(work_db):
    """Look for WorkItems in `work_db` that should not be mutated due to spor metadata.

    For each WorkItem, find anchors for the item's file/line/columns. If an
    anchor exists with metadata containing `{mutate: False}` then the WorkItem
    is marked as SKIPPED.
    """
    for item in work_db.work_items:
        try:
            anchors = tuple(find_anchors(item.filename))
        except ValueError:
            log.info('No spor repository for %s', item.filename)
            continue

        for anchor in anchors:
            metadata = anchor.metadata
            if item.line_number == anchor.line_number and not metadata.get('mutate', True):
                item.worker_outcome = WorkerOutcome.SKIPPED
                log.info('skipping %s', item)
                work_db.update_work_item(item)
