"Implementation of various formatting commands."

import json
import sys
import xml.etree.ElementTree

import docopt
from yattag import Doc

from cosmic_ray.reporting import create_report, is_killed, survival_rate
from cosmic_ray.testing.test_runner import TestOutcome
from cosmic_ray.util import pairwise, index_of_first_difference
from cosmic_ray.work_item import WorkItem, WorkItemJsonDecoder
from cosmic_ray.worker import WorkerOutcome

CHARACTER_DIFF_MARKER = '^'

DIFF_ADDED_MARKER = '+'

DIFF_REMOVED_MARKER = '-'


def format_survival_rate():
    """cr-rate

Usage: cr-rate

Read JSON work-records from stdin and print the survival rate.
"""
    records = (WorkItem(json.loads(line, cls=WorkItemJsonDecoder)) for line in sys.stdin)
    print('{:.2f}'.format(survival_rate(records)))


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
    records = (WorkItem(json.loads(line, cls=WorkItemJsonDecoder)) for line in sys.stdin)
    for line in create_report(records, show_pending, full_report):
        print(line)


def _create_element_from_item(work_item):
    data = work_item.data
    sub_elem = xml.etree.ElementTree.Element('testcase')

    sub_elem.set('classname', work_item.job_id)
    sub_elem.set('line', str(work_item.line_number))
    sub_elem.set('file', work_item.module)
    if work_item.command_line:
        sub_elem.set('name', str(work_item.command_line))

    outcome = work_item.worker_outcome

    if outcome == WorkerOutcome.TIMEOUT:
        error_elem = xml.etree.ElementTree.SubElement(sub_elem, 'error')
        error_elem.set('message', "Timeout: {:.3f} sec".format(data))
    elif outcome == WorkerOutcome.EXCEPTION:
        error_elem = xml.etree.ElementTree.SubElement(sub_elem, 'error')
        error_elem.set('message', "Worker has encountered exception")
        error_elem.text = str(data) + "\n".join(work_item.diff)
    elif _evaluation_success(outcome, work_item):
        failure_elem = xml.etree.ElementTree.SubElement(sub_elem, 'failure')
        failure_elem.set('message', "Mutant has survived your unit tests")
        failure_elem.text = str(data) + "\n".join(work_item.diff)

    return sub_elem


def _evaluation_success(outcome, work_item):
    return outcome == WorkerOutcome.NORMAL and \
           work_item.test_outcome in [TestOutcome.SURVIVED,
                                      TestOutcome.INCOMPETENT]


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
    records = (WorkItem(json.loads(line, cls=WorkItemJsonDecoder)) for line in sys.stdin)
    xml_elem = _create_xml_report(records)
    xml_elem.write(sys.stdout.buffer, encoding='utf-8', xml_declaration=True)




def markup_character_level_diff(diff):
    if len(diff) == 0:
        return diff
    new_diff = [diff[0]]
    for line_a, line_b in pairwise(diff):
        new_diff.append(line_b)
        if line_a.startswith(DIFF_REMOVED_MARKER) and line_b.startswith(DIFF_ADDED_MARKER):
            diff_character_index = index_of_first_difference(
                line_a[len(DIFF_REMOVED_MARKER):],
                line_b[len(DIFF_ADDED_MARKER):])
            diff_character_marker = (' ' * (len(DIFF_ADDED_MARKER)
                                           + diff_character_index)
                                     + CHARACTER_DIFF_MARKER)
            new_diff.append(diff_character_marker)
    return new_diff


def diff_without_header(diff):
    return diff[4:]


def pycharm_url(filename, line_number):
    return 'pycharm://open?file={}&line={}'.format(filename, line_number)


def report_html():
    doc, tag, text = Doc().tagtext()
    doc.asis('<!DOCTYPE html>')
    with tag('html', lang='en'):
        with tag('head'):
            doc.stag('meta', charset='utf-8')
            doc.stag('meta', name='viewport', content='width=device-width, initial-scale=1, shrink-to-fit=no')
            doc.stag('link',
                     rel='stylesheet',
                     href='https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css',
                     integrity='sha384-WskhaSGFgHYWDcbwN70/dfYBj47jz9qbsMId/iRN3ewGhXQFZCSftd1LZCfmhktB',
                     crossorigin='anonymous')
            with tag('title'):
                text('Cosmic Ray Report')
        with tag('body'):
            with tag('h1'):
                text('Cosmic Ray Report')

            work_items = (WorkItem(json.loads(line, cls=WorkItemJsonDecoder)) for line in sys.stdin)

            for index, work_item in enumerate(work_items, start=1):
                with tag('div', klass='container work-item'):
                    with tag('h4', klass='job_id'):
                        text('{} : job ID {}'.format(index, work_item.job_id))
                    if work_item.test_outcome == TestOutcome.SURVIVED:
                        with tag('div', klass='alert alert-danger test-outcome', role='alert'):
                            text('Survived!')
                    elif work_item.test_outcome == TestOutcome.INCOMPETENT:
                        with tag('div', klass='alert alert-info test-outcome', role='alert'):
                            text('Incompetent.')
                    elif work_item.test_outcome == TestOutcome.KILLED:
                         with tag('div', klass='alert alert-success test-outcome', role='alert'):
                            text('Killed.')

                    if work_item.command_line:
                        with tag('pre', klass='command-line'):
                            text(work_item.command_line)

                    with tag('a', href=pycharm_url(
                        work_item.filename,
                        work_item.line_number)):
                        with tag('pre', klass='location'):
                            text('{}:{}:{}'.format(
                                work_item.filename,
                                work_item.line_number,
                                work_item.col_offset
                            ))
                    if work_item.diff:
                        diff = markup_character_level_diff(diff_without_header(work_item.diff))
                        with tag('pre', klass='diff'):
                            text('\n'.join(diff))

            doc.stag('script',
                     src='https://code.jquery.com/jquery-3.3.1.slim.min.js',
                     integrity='sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo',
                     crossorigin='anonymous')
            doc.stag('script',
                     src='https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js',
                     integrity='sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49',
                     crossorigin='anonymous')
            doc.stag('script',
                     src='https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.min.js',
                     integrity='sha384-smHYKdLADwkXOn1EmN1qk/HfnUcbVRZyYmZ4qpPea6sjB/pTJ0euyQp0Mk8ck+5T',
                     crossorigin='anonymous')

    print(doc.getvalue())
