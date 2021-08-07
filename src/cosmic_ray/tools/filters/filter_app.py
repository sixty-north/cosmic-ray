"""A simple base for creating common types of work-db filters.
"""
import argparse
import logging
import sys

from exit_codes import ExitCode

from cosmic_ray.work_db import use_db


class FilterApp:
    """Base class for simple WorkDB filters.

    This provides command-line handling for common filter options like
    the session and verbosity level. Subclasses can add their own arguments
    as well. This provides a `main()` function that open the session's WorkDB
    and passes it to the subclass's `filter()` function.

    **It is by no means required that you inherit from or otherwise use
    this class in order to build a filter.** You can build a filter using
    any technique you want. Typically all a filter does is modify a session
    database in some way, so you can use the Cosmic Ray API for that directly
    if you want.
    """

    def add_args(self, parser: argparse.ArgumentParser):
        """Add any arguments that the subclass needs to the parser.

        Args:
            parser: The ArgumentParser for command-line processing.
        """

    def description(self):
        """The description of the filter.

        This is used for the command-line help message.
        """
        return None

    def main(self, argv=None):
        """The main function for the app.

        Args:
            argv: Command line argument list of parse.
        """
        if argv is None:
            argv = sys.argv[1:]

        parser = argparse.ArgumentParser(
            description=self.description(),
        )
        parser.add_argument(
            'session', help="Path to the session on which to operate")
        parser.add_argument(
            '--verbosity', help='Verbosity level for logging', default='WARNING')
        self.add_args(parser)
        args = parser.parse_args(argv)

        logging.basicConfig(level=getattr(logging, args.verbosity))

        with use_db(args.session) as db:
            self.filter(db, args)

        return ExitCode.OK

    def filter(self, work_db, args):
        """Apply this filter to a WorkDB.

        This should modify the WorkDB in place.

        Args:
            work_db: An open WorkDB instance.
            args: The argparse Namespace for the command line.
        """
        raise NotImplementedError()
