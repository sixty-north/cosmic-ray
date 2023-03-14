import nox

nox.options.sessions = ["tests-3.11"]


@nox.session(python=["3.7", "3.8", "3.9", "3.10", "3.11"])
def tests(session):
    session.install(".[test]")
    command = ["pytest", "tests"] + list(session.posargs)
    session.run(*command)


@nox.session
def lint(session):
    session.install(".[dev]")
    session.run(*("flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics".split()))
    session.run(*("flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics".split()))