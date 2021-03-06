import functools
import os

import nox

nox.options.envdir = "build/nox"

VERSIONS = ["3.8", "3.9"]

@nox.session(python=VERSIONS)
def tests(session):
    """Run test suite with pytest."""
    tmpdir = session.create_tmp()
    session.install(".[test]")
    tests = session.posargs or ["seasonable.tests"]
    session.run(
        "coverage",
        "run",
        "--branch",
        "--source=seasonable",
        "--omit=**/__main__.py",
        "-m",
        "virtue",
        *tests,
        env=dict(COVERAGE_FILE=os.path.join(tmpdir, "coverage"), TMPDIR=tmpdir),
    )
    fail_under = "--fail-under=100"
    session.run(
        "coverage",
        "report",
        fail_under,
        "--show-missing",
        "--skip-covered",
        env=dict(COVERAGE_FILE=os.path.join(tmpdir, "coverage")),
    )


@nox.session(python=VERSIONS[-1])
def lint(session):
    files = ["src/", "noxfile.py", "setup.py"]
    session.install("-e", ".[lint]")
    session.run("black", "--check", "--diff", *files)
    black_compat = ["--max-line-length=88", "--ignore=E203"]
    session.run("flake8", *black_compat, "src/pycus")
    session.run("bandit", "src/pycus")
    session.run(
        "mypy",
        "--disallow-untyped-defs",
        "--warn-unused-ignores",
        "--ignore-missing-imports",
        "src/",
    )


@nox.session(python=VERSIONS[-1])
def docs(session):
    """Build the documentation."""
    output_dir = os.path.abspath(os.path.join(session.create_tmp(), "output"))
    doctrees, html = map(
        functools.partial(os.path.join, output_dir), ["doctrees", "html"]
    )
    session.run("rm", "-rf", output_dir, external=True)
    session.install(".[doc]")
    sphinx = ["sphinx-build", "-b", "html", "-W", "-d", doctrees, ".", html]
    session.cd("doc")
    session.run(*sphinx)
