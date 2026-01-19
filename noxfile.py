"""Nox sessions."""

import os
import shlex
import shutil
from pathlib import Path
from textwrap import dedent

import nox
from nox import session
from nox.sessions import Session

# DJANGO_STABLE_VERSION should be set to the latest Django LTS version

DJANGO_STABLE_VERSION = "5.2"
DJANGO_VERSIONS = [
    "4.2",
    "5.1",
    "5.2",
    "6.0",
]

# PYTHON_STABLE_VERSION should be set to the latest stable Python version

PYTHON_STABLE_VERSION = "3.13"
PYTHON_VERSIONS = ["3.11", "3.12", "3.13", "3.14"]


PACKAGE = "django_tomselect"

nox.needs_version = ">= 2024.4.15"
nox.options.sessions = (
    "pre-commit",
    "safety",
    "tests",
    "xdoctest",
    "docs-build",
)
nox.options.default_venv_backend = "uv"


def activate_virtualenv_in_precommit_hooks(session: Session) -> None:
    """Activate virtualenv in hooks installed by pre-commit.

    This function patches git hooks installed by pre-commit to activate the
    session's virtual environment. This allows pre-commit to locate hooks in
    that environment when invoked from git.

    Args:
        session: The Session object.
    """
    assert session.bin is not None  # nosec

    # Only patch hooks containing a reference to this session's bindir. Support
    # quoting rules for Python and bash, but strip the outermost quotes so we
    # can detect paths within the bindir, like <bindir>/python.
    bindirs = [
        bindir[1:-1] if bindir[0] in "'\"" else bindir for bindir in (repr(session.bin), shlex.quote(session.bin))
    ]

    virtualenv = session.env.get("VIRTUAL_ENV")
    if virtualenv is None:
        return

    headers = {
        # pre-commit < 2.16.0
        "python": f"""\
            import os
            os.environ["VIRTUAL_ENV"] = {virtualenv!r}
            os.environ["PATH"] = os.pathsep.join((
                {session.bin!r},
                os.environ.get("PATH", ""),
            ))
            """,
        # pre-commit >= 2.16.0
        "bash": f"""\
            VIRTUAL_ENV={shlex.quote(virtualenv)}
            PATH={shlex.quote(session.bin)}"{os.pathsep}$PATH"
            """,
        # pre-commit >= 2.17.0 on Windows forces sh shebang
        "/bin/sh": f"""\
            VIRTUAL_ENV={shlex.quote(virtualenv)}
            PATH={shlex.quote(session.bin)}"{os.pathsep}$PATH"
            """,
    }

    hookdir = Path(".git") / "hooks"
    if not hookdir.is_dir():
        return

    for hook in hookdir.iterdir():
        if hook.name.endswith(".sample") or not hook.is_file():
            continue

        if not hook.read_bytes().startswith(b"#!"):
            continue

        text = hook.read_text()

        if not any(Path("A") == Path("a") and bindir.lower() in text.lower() or bindir in text for bindir in bindirs):
            continue

        lines = text.splitlines()

        for executable, header in headers.items():
            if executable in lines[0].lower():
                lines.insert(1, dedent(header))
                hook.write_text("\n".join(lines))
                break


@session(name="pre-commit", python=PYTHON_STABLE_VERSION)
@nox.parametrize("django", DJANGO_STABLE_VERSION)
def precommit(session: Session, django: str) -> None:
    """Lint using pre-commit."""
    args = session.posargs or [
        "run",
        "--all-files",
        "--hook-stage=manual",
        "--show-diff-on-failure",
    ]
    session.install(
        "bandit",
        "ruff",
        "darglint",
        "flake8",
        "flake8-bugbear",
        "flake8-docstrings",
        "flake8-rst-docstrings",
        "pep8-naming",
        "pre-commit",
        "pre-commit-hooks",
        "pyupgrade",
    )
    session.run("pre-commit", *args)
    if args and args[0] == "install":
        activate_virtualenv_in_precommit_hooks(session)


@session(python=PYTHON_STABLE_VERSION)
@nox.parametrize("django", DJANGO_STABLE_VERSION)
def safety(session: Session, django: str) -> None:
    """Scan dependencies for insecure packages."""
    requirements = session.posargs or ["requirements.txt"]
    session.install("safety")
    session.run("safety", "check", "--full-report", f"--file={requirements}")


@session(python=PYTHON_VERSIONS)
@nox.parametrize("django", DJANGO_VERSIONS)
def tests(session: Session, django: str) -> None:
    """Run the test suite."""
    # Skip incompatible Python/Django combinations
    if django == "6.0" and session.python == "3.11":
        session.skip("Django 6.0 requires Python 3.12+")

    session.install(".[dev]")
    session.install(f"django~={django}.0")
    try:
        session.run("coverage", "run", "-m", "pytest", "-vv", *session.posargs)
    finally:
        if session.interactive:
            session.notify("coverage", posargs=[])


@session(python=PYTHON_STABLE_VERSION)
@nox.parametrize("django", DJANGO_STABLE_VERSION)
def coverage(session: Session, django: str) -> None:
    """Produce the coverage report."""
    args = session.posargs or ["report"]

    session.install("coverage[toml]")

    if not session.posargs and any(Path().glob(".coverage.*")):
        session.run("coverage", "combine")

    session.run("coverage", *args)


@session(python=PYTHON_STABLE_VERSION)
@nox.parametrize("django", DJANGO_STABLE_VERSION)
def xdoctest(session: Session, django: str) -> None:
    """Run examples with xdoctest."""
    if session.posargs:
        args = [PACKAGE, *session.posargs]
    else:
        args = [f"--modname={PACKAGE}", "--command=all"]
        if "FORCE_COLOR" in os.environ:
            args.append("--colored=1")

    session.install(".")
    session.install("xdoctest[colors]")
    session.run("python", "-m", "xdoctest", *args)


@session(name="docs-build", python=PYTHON_STABLE_VERSION)
@nox.parametrize("django", DJANGO_STABLE_VERSION)
def docs_build(session: Session, django: str) -> None:
    """Build the documentation."""
    args = session.posargs or ["docs", "docs/_build"]
    if not session.posargs and "FORCE_COLOR" in os.environ:
        args.insert(0, "--color")

    session.install(".")
    session.install("-r", "docs/requirements.txt")

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-build", *args)


@session(python=PYTHON_STABLE_VERSION)
@nox.parametrize("django", DJANGO_STABLE_VERSION)
def docs(session: Session, django: str) -> None:
    """Build and serve the documentation with live reloading on file changes."""
    args = session.posargs or ["--open-browser", "docs", "docs/_build"]
    session.install(".")
    session.install("-r", "docs/requirements.txt")
    session.install("sphinx-autobuild")

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-autobuild", *args)
