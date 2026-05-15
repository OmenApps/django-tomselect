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
    "js-lint",
    "pip-audit",
    "npm-audit",
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


@session(name="js-build", python=False)
def js_build(session: Session) -> None:
    """Install npm dependencies and build static JavaScript bundles."""
    session.run("npm", "install", external=True)
    session.run("npm", "run", "build", external=True)
    session.run("npm", "run", "buildsmall", external=True)


#: Bootstrap 5 CSS variable fallbacks (Bootstrap 5.3 defaults).
#: Order matters: longer names must come before shorter ones that are prefixes
#: (e.g. --bs-border-color-translucent before --bs-border-color).
_BS5_FALLBACKS: list[tuple[str, str]] = [
    ("--bs-border-color-translucent", "rgba(0, 0, 0, 0.175)"),
    ("--bs-border-color", "#dee2e6"),
    ("--bs-border-radius-sm", "0.25rem"),
    ("--bs-border-radius-lg", "0.5rem"),
    ("--bs-border-radius", "0.375rem"),
    ("--bs-border-width", "1px"),
    ("--bs-body-bg", "#fff"),
    ("--bs-body-color", "#212529"),
    ("--bs-secondary-bg", "#e9ecef"),
    ("--bs-secondary-color", "#a7aeb8"),
    ("--bs-tertiary-bg", "#f8f9fa"),
    ("--bs-form-invalid-color", "#dc3545"),
    ("--bs-form-valid-color", "#198754"),
    ("--bs-box-shadow-inset", "inset 0 1px 2px rgba(0, 0, 0, 0.075)"),
]

#: Invalid color-mix() calls emitted by upstream tom-select and their fixes.
_COLOR_MIX_FIXES: list[tuple[str, str]] = [
    ("color-mix(#fff, #d0d0d0, 85%)", "color-mix(in srgb, #fff 85%, #d0d0d0)"),
    ("color-mix(#1da7ee, #178ee9, 60%)", "color-mix(in srgb, #1da7ee 60%, #178ee9)"),
    ("color-mix(#008fd8, #0075cf, 60%)", "color-mix(in srgb, #008fd8 60%, #0075cf)"),
    ("color-mix(#fefefe, #f2f2f2, 60%)", "color-mix(in srgb, #fefefe 60%, #f2f2f2)"),
]


def _patch_bs5_fallbacks(css: str) -> str:
    """Add fallback values to ``var(--bs-*)`` calls that lack them."""
    import re

    for var_name, fallback in _BS5_FALLBACKS:
        # Match var(--bs-xxx) but NOT var(--bs-xxx, already-has-fallback).
        # Negative lookahead ensures we skip calls that already include a comma.
        pattern = re.compile(re.escape(f"var({var_name})"))
        css = pattern.sub(f"var({var_name}, {fallback})", css)
    return css


def _patch_color_mix(css: str) -> str:
    """Fix invalid color-mix() syntax (missing 'in srgb' color space)."""
    for bad, good in _COLOR_MIX_FIXES:
        css = css.replace(bad, good)
    # Handle BS5 variant that may already have had var() fallbacks inserted.
    import re

    css = re.sub(
        r"color-mix\(var\(--bs-body-bg(?:,\s*[^)]+)?\),\s*#d0d0d0,\s*85%\)",
        lambda m: m.group().replace("color-mix(", "color-mix(in srgb, ").replace(", #d0d0d0, 85%", " 85%, #d0d0d0"),
        css,
    )
    return css


@session(name="css-vendor", python=False)
def css_vendor(session: Session) -> None:
    """Copy tom-select CSS from node_modules and patch for standalone use.

    Copies CSS for all three themes (default, bootstrap4, bootstrap5),
    adds fallback values to Bootstrap 5 CSS variables so the widget
    renders without Bootstrap loaded, fixes invalid color-mix() syntax,
    and regenerates minified files.
    """
    src = Path("node_modules/tom-select/dist/css")
    dest = Path("src/django_tomselect/static/django_tomselect/vendor/tom-select/css")

    if not src.exists():
        session.error("node_modules/tom-select not found - run 'npm install' first")

    themes = ("default", "bootstrap4", "bootstrap5")

    # 1. Copy all files from npm
    for theme in themes:
        for suffix in (".css", ".min.css", ".css.map", ".min.css.map"):
            name = f"tom-select.{theme}{suffix}"
            session.log(f"Copying {name}")
            shutil.copy2(src / name, dest / name)

    # 2. Patch unminified CSS files
    for theme in themes:
        css_path = dest / f"tom-select.{theme}.css"
        css = css_path.read_text()

        css = _patch_color_mix(css)
        if theme == "bootstrap5":
            css = _patch_bs5_fallbacks(css)

        css_path.write_text(css)
        session.log(f"Patched tom-select.{theme}.css")

    # 3. Regenerate minified files
    for theme in themes:
        css_file = f"tom-select.{theme}.css"
        min_file = f"tom-select.{theme}.min.css"
        session.run(
            "npx",
            "esbuild",
            str(dest / css_file),
            "--minify",
            f"--outfile={dest / min_file}",
            "--allow-overwrite",
            external=True,
        )
        session.log(f"Minified {min_file}")


@session(name="js-lint", python=False)
def js_lint(session: Session) -> None:
    """Lint JavaScript with StandardJS."""
    session.run("npm", "run", "lint", *session.posargs, external=True)


@session(name="pip-audit", python=PYTHON_STABLE_VERSION)
@nox.parametrize("django", DJANGO_STABLE_VERSION)
def pip_audit(session: Session, django: str) -> None:
    """Scan dependencies for insecure packages."""
    session.install(".[dev]")
    session.install("pip-audit")
    session.run("pip-audit", *session.posargs)


@session(name="npm-audit", python=False)
def npm_audit(session: Session) -> None:
    """Scan npm dependencies for security vulnerabilities."""
    session.run("npm", "audit", "--audit-level=high", *session.posargs, external=True)


@session(python=PYTHON_VERSIONS)
@nox.parametrize("django", DJANGO_VERSIONS)
def tests(session: Session, django: str) -> None:
    """Run the test suite."""
    # Skip incompatible Python/Django combinations
    if django == "6.0" and session.python == "3.11":
        session.skip("Django 6.0 requires Python 3.12+")

    session.install(".[dev]")
    session.install(f"django~={django}.0")
    posargs = list(session.posargs)
    has_marker_filter = "-m" in posargs or any(arg.startswith("-m=") for arg in posargs)
    args = posargs if has_marker_filter else ["-m", "not playwright", *posargs]
    try:
        session.run("coverage", "run", "-m", "pytest", "-vv", *args)
    finally:
        if session.interactive:
            session.notify("coverage", posargs=[])


@session(name="tests-browser", python=PYTHON_STABLE_VERSION)
@nox.parametrize("django", DJANGO_STABLE_VERSION)
def tests_browser(session: Session, django: str) -> None:
    """Run the Playwright browser regression tests."""
    session.install(".[dev]")
    session.install(f"django~={django}.0")

    browser_cache = Path(".nox", "playwright-browsers")
    session.env["PLAYWRIGHT_BROWSERS_PATH"] = str(browser_cache.resolve())

    session.run("playwright", "install", "chromium")

    posargs = list(session.posargs)
    has_marker_filter = "-m" in posargs or any(arg.startswith("-m=") for arg in posargs)
    has_explicit_target = any(
        not arg.startswith("-") and (arg.endswith(".py") or "::" in arg or Path(arg.split("::")[0]).exists())
        for arg in posargs
    )
    args = posargs
    if not has_marker_filter:
        args = ["-m", "playwright", *args]
    if not has_explicit_target:
        args = [*args, "example_project/test_browser.py"]

    session.run("pytest", *args)


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
