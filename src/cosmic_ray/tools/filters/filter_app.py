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
    """
    def add_args(self, parser: argparse.ArgumentParser):
        """Add any arguments that the subclass needs to the parser.

        Args:
            parser: The ArgumentParser for command-line processing.
        """
        pass

    def description(self):
        """The description of the filter.

        This is used for the command-line help message.
        """
        return None

    def main(self, argv=None):
        if argv is None:
            argv = sys.argv[1:]

        parser = argparse.ArgumentParser(
            description=self.description(),
        )
        parser.add_argument('session', help="Path to the session on which to operate")
        parser.add_argument('--verbosity', help='Verbosity level for logging', default='WARNING')
        self.add_args(parser)
        args = parser.parse_args(argv)

        logging.basicConfig(level=getattr(logging, args.verbosity))

        with use_db(args.session) as db:
            self.filter(db, args)

        return ExitCode.OK

    def filter(self, work_db):
        raise NotImplementedError()

