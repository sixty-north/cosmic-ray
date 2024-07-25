import nox

nox.options.sessions = ["tests-3.11"]


@nox.session(python=["3.7", "3.8", "3.9", "3.10", "3.11", "3.12"])
def tests(session: nox.Session):
    session.install("-r", "requirements-dev.lock")
    command = ["pytest", "tests"] + list(session.posargs)
    session.run(*command)


@nox.session
def lint(session):
    session.install("-r", "requirements-dev.lock")

    session.log("Checking syntax with flake8")
    check_syntax = "python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics"
    session.run(*check_syntax.split())

    session.log("Checking style with flake8")
    check_style = "python -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics"
    session.run(*check_style.split())
