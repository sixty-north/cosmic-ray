"A tool for generating HTML reports."

from itertools import chain

import docopt
from yattag import Doc

from cosmic_ray.work_db import WorkDB, use_db
from cosmic_ray.work_item import TestOutcome


def report_html():
    """cr-html

Usage: cr-html <session-file>

Print an HTML formatted report of test results.
"""
    arguments = docopt.docopt(report_html.__doc__, version='cr-rate 1.0')
    with use_db(arguments['<session-file>'], WorkDB.Mode.open) as db:
        doc = _generate_html_report(db)

    print(doc.getvalue())


def _generate_html_report(db):
    # pylint: disable=too-many-statements
    doc, tag, text = Doc().tagtext()
    doc.asis('<!DOCTYPE html>')
    with tag('html', lang='en'):
        with tag('head'):
            doc.stag('meta', charset='utf-8')
            doc.stag(
                'meta',
                name='viewport',
                content='width=device-width, initial-scale=1, shrink-to-fit=no'
            )
            doc.stag(
                'link',
                rel='stylesheet',
                href='https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css',
                integrity='sha384-WskhaSGFgHYWDcbwN70/dfYBj47jz9qbsMId/iRN3ewGhXQFZCSftd1LZCfmhktB',
                crossorigin='anonymous')
            with tag('title'):
                text('Cosmic Ray Report')
        with tag('body'):
            with tag('h1'):
                text('Cosmic Ray Report')

            completed = db.completed_work_items
            incomplete = ((item, None) for item in db.pending_work_items)
            all_items = chain(completed, incomplete)

            for index, (work_item, result) in enumerate(all_items, start=1):
                with tag('div', klass='container work-item'):
                    with tag('h4', klass='job_id'):
                        text('{} : job ID {}'.format(index, work_item.job_id))

                    if result is not None:
                        if result.is_killed:
                            if result.test_outcome == TestOutcome.INCOMPETENT:
                                level = 'info'
                            else:
                                level = 'success'
                        else:
                            level = 'danger'

                        with tag(
                                'div',
                                klass='alert alert-{} test-outcome'.format(
                                    level),
                                role='alert'):
                            if not result.is_killed:
                                with tag('p'):
                                    text('SURVIVED')
                            with tag('p'):
                                text('worker outcome: {}'.format(
                                    result.worker_outcome))
                            with tag('p'):
                                text('test outcome: {}'.format(
                                    result.test_outcome))

                    with tag(
                            'a',
                            href=pycharm_url(
                                str(work_item.module_path),
                                work_item.start_pos[0])):
                        with tag('pre', klass='location'):
                            text('{}, start pos: {}, end pos: {}'.format(
                                work_item.module_path, work_item.start_pos,
                                work_item.end_pos))

                    with tag('pre'):
                        text('operator: {}, occurrence: {}'.format(
                            work_item.operator_name, work_item.occurrence))

                    if result is not None:
                        if result.diff:
                            with tag('div', klass='alert alert-secondary'):
                                with tag('pre', klass='diff'):
                                    text(result.diff)

                        if result.output:
                            with tag('div', klass='alert alert-secondary'):
                                with tag('pre', klass='diff'):
                                    text(result.output)

            doc.stag(
                'script',
                src='https://code.jquery.com/jquery-3.3.1.slim.min.js',
                integrity='sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo',
                crossorigin='anonymous')
            doc.stag(
                'script',
                src='https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js',
                integrity='sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49',
                crossorigin='anonymous')
            doc.stag(
                'script',
                src='https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.min.js',
                integrity='sha384-smHYKdLADwkXOn1EmN1qk/HfnUcbVRZyYmZ4qpPea6sjB/pTJ0euyQp0Mk8ck+5T',
                crossorigin='anonymous')

    return doc


def pycharm_url(filename, line_number):
    "Get a URL for opening a file in Pycharm."
    return 'pycharm://open?file={}&line={}'.format(filename, line_number)


#
