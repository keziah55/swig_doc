from pathlib import Path
import nox

ROOT_DIR = Path(__file__).parent

SRC_DIR = ROOT_DIR.joinpath("swig_doc")
TEST_DIR = ROOT_DIR.joinpath("tests")
COV_DIR = ROOT_DIR.joinpath("coverage_report")

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]


def tests(session):
    """Run test suite."""

    session.install("--group", "base", "--group", "test")
    session.run(
        "pytest",
        "-v",
        TEST_DIR,
        f"--cov={SRC_DIR}",
        "--cov-report",
        f"html:{COV_DIR}",
    )


def lint(session):
    """Run flake8."""

    session.install("flake8")
    session.run("flake8", SRC_DIR, TEST_DIR)
