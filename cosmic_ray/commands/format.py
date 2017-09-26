from cosmic_ray.testing.test_runner import TestOutcome
from cosmic_ray.work_record import WorkRecord
from cosmic_ray.worker import WorkerOutcome
import docopt
import json
import sys
import xml.etree.ElementTree


def _print_item(work_record, full_report):
    data = work_record.data
    outcome = work_record.worker_outcome
    if outcome in [WorkerOutcome.NORMAL, WorkerOutcome.EXCEPTION]:
        outcome = work_record.test_outcome
    ret_val = [
        'job ID {}:{}:{}'.format(
            work_record.job_id,
            outcome,
            work_record.module),
        'command: {}'.format(
            ' '.join(work_record.command_line)
            if work_record.command_line is not None else ''),
    ]
    if outcome == TestOutcome.KILLED and not full_report:
        ret_val = []
    elif work_record.worker_outcome == WorkerOutcome.TIMEOUT:
        if full_report:
            ret_val.append("timeout: {:.3f} sec".format(data))
        else:
            ret_val = []
    elif work_record.worker_outcome in [WorkerOutcome.NORMAL, WorkerOutcome.EXCEPTION]:
        ret_val += data
        ret_val += work_record.diff

    # for presentation purposes only
    if ret_val:
        ret_val.append('')

    return ret_val


def is_killed(record):
    if record.worker_outcome == WorkerOutcome.TIMEOUT:
        return True
    elif record.worker_outcome == WorkerOutcome.NORMAL:
        if record.test_outcome == TestOutcome.KILLED:
            return True
    return False


def create_report(records, show_pending, full_report=False):
    total_jobs = 0
    pending_jobs = 0
    kills = 0
    for item in records:
        total_jobs += 1
        if item.worker_outcome is None:
            pending_jobs += 1
        if is_killed(item):
            kills += 1
        if (item.worker_outcome is not None) or show_pending:
            yield from _print_item(item, full_report)

    completed_jobs = total_jobs - pending_jobs

    yield 'total jobs: {}'.format(total_jobs)

    if completed_jobs > 0:
        yield 'complete: {} ({:.2f}%)'.format(
            completed_jobs, completed_jobs / total_jobs * 100)
        yield 'survival rate: {:.2f}%'.format(
            (1 - kills / completed_jobs) * 100)
    else:
        yield 'no jobs completed'


def survival_rate():
    """cr-rate

Usage: cr-rate

Read JSON work-records from stdin and print the survival rate.
"""
    records = (WorkRecord(json.loads(line)) for line in sys.stdin)

    total_jobs = 0
    pending_jobs = 0
    kills = 0
    for item in records:
        total_jobs += 1
        if item.worker_outcome is None:
            pending_jobs += 1
        if is_killed(item):
            kills += 1

    completed_jobs = total_jobs - pending_jobs

    if not completed_jobs:
        rate = 0
    else:
        rate = (1 - kills / completed_jobs) * 100

    print('{:.2f}'.format(rate))


def report():
    """cr-report

Usage: cr-report [--full-report] [--show-pending]

Print a nicely formatted report of test results and some basic statistics.

options:
    --full-report   Show test output and mutation diff for killed mutants
    --show-pending  Display results for incomplete tasks
"""

    arguments = docopt.docopt(report.__doc__, version='cr-format 0.1')
    full_report = arguments['--full-report']
    show_pending = arguments['--show-pending']
    records = (WorkRecord(json.loads(line)) for line in sys.stdin)
    for line in create_report(records, show_pending, full_report):
        print(line)


def _create_element_from_item(work_record):
    data = work_record.data
    sub_elem = xml.etree.ElementTree.Element('testcase')

    sub_elem.set('classname', work_record.job_id)
    sub_elem.set('line', str(work_record.line_number))
    sub_elem.set('file', work_record.module)
    if work_record.command_line:
        sub_elem.set('name', str(work_record.command_line))

    outcome = work_record.worker_outcome

    if outcome == WorkerOutcome.TIMEOUT:
        error_elem = xml.etree.ElementTree.SubElement(sub_elem, 'error')
        error_elem.set('message', "Timeout: {:.3f} sec".format(data))
    elif outcome == WorkerOutcome.EXCEPTION:
        error_elem = xml.etree.ElementTree.SubElement(sub_elem, 'error')
        error_elem.set('message', "Worker has encountered exception")
        error_elem.text = str(data) + "\n".join(work_record.diff)
    elif (outcome == WorkerOutcome.NORMAL and
          work_record.test_outcome in [TestOutcome.SURVIVED, TestOutcome.INCOMPETENT]):
        failure_elem = xml.etree.ElementTree.SubElement(sub_elem, 'failure')
        failure_elem.set('message', "Mutant has survived your unit tests")
        failure_elem.text = str(data) + "\n".join(work_record.diff)

    return sub_elem


def _create_xml_report(records):
    total_jobs = 0
    errors = 0
    failed = 0
    root_elem = xml.etree.ElementTree.Element('testsuite')
    for item in records:
        total_jobs += 1
        if item.worker_outcome is None:
            errors += 1
        if is_killed(item):
            failed += 1
        if item.worker_outcome is not None:
            subelement = _create_element_from_item(item)
            root_elem.append(subelement)

    root_elem.set('errors', str(errors))
    root_elem.set('failures', str(failed))
    root_elem.set('skips', str(0))
    root_elem.set('tests', str(total_jobs))
    return xml.etree.ElementTree.ElementTree(root_elem)


def report_xml():
    """cr-xml

Usage: cr-xml

Print an XML formatted report of test results for continuos integration systems
"""
    records = (WorkRecord(json.loads(line)) for line in sys.stdin)
    xml_elem = _create_xml_report(records)
    xml_elem.write(sys.stdout.buffer, encoding='utf-8', xml_declaration=True)
