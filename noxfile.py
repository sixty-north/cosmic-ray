import argparse
import nox

nox.options.sessions = ["tests-3.11"]


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12"])
def tests(session):
    session.install(".[test]")
    command = ["pytest", "tests"] + list(session.posargs)
    session.run(*command)


@nox.session
def lint(session):
    session.install(".[dev]")

    session.log("Checking syntax with flake8")
    check_syntax = "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics"
    session.run(*check_syntax.split())

    session.log("Checking style with flake8")
    check_style = "flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics"
    session.run(*check_style.split())


@nox.session
def release(session: nox.Session) -> None:
    """
    Kicks off an automated release process by creating and pushing a new tag.

    Invokes bump2version with the posarg setting the version.

    Usage:
    $ nox -s release -- [major|minor|patch]
    """
    parser = argparse.ArgumentParser(description="Release a semver version.")
    parser.add_argument(
        "version",
        type=str,
        nargs=1,
        help="The type of semver release to make.",
        choices={"major", "minor", "patch"},
    )
    args: argparse.Namespace = parser.parse_args(args=session.posargs)
    version: str = args.version.pop()

    # If we get here, we should be good to go
    # Let's do a final check for safety
    confirm = input(
        f"You are about to bump the {version!r} version. Are you sure? [y/n]: "
    )

    # Abort on anything other than 'y'
    if confirm.lower().strip() != "y":
        session.error(f"You said no when prompted to bump the {version!r} version.")

    session.install("bump2version")

    session.log(f"Bumping the {version!r} version")
    session.run("bump2version", version)

    session.log("Pushing the new tag")
    session.run("git", "push", external=True)
    session.run("git", "push", "--tags", external=True)
