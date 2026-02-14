"""
Tests that CLI entry points are properly installed and accessible.

These tests are environment-agnostic: they work whether the package was
installed via pip, pixi, conda, or any other method. They verify that the
currently active environment exposes the expected console scripts.
"""

import importlib.metadata
import shutil
import subprocess

import pytest

CONSOLE_SCRIPTS = ["combine_postfits", "combine_postfits_cov"]


@pytest.mark.parametrize("name", CONSOLE_SCRIPTS)
def test_entry_point_registered(name):
    """Verify that the entry point is declared in package metadata."""
    eps = importlib.metadata.entry_points()
    # Python 3.12+ returns a SelectableGroups; 3.9–3.11 returns a dict
    if hasattr(eps, "select"):
        console_scripts = eps.select(group="console_scripts")
    else:
        console_scripts = eps.get("console_scripts", [])
    registered_names = [ep.name for ep in console_scripts]
    assert name in registered_names, (
        f"'{name}' not found in console_scripts entry points. Registered: {registered_names}"
    )


@pytest.mark.parametrize("name", CONSOLE_SCRIPTS)
def test_executable_on_path(name):
    """Verify that the executable is findable on $PATH."""
    location = shutil.which(name)
    assert location is not None, f"'{name}' not found on $PATH. Make sure the package is installed (pip install -e .)."


@pytest.mark.parametrize("name", CONSOLE_SCRIPTS)
def test_executable_runs(name):
    """Verify that the executable launches and prints help."""
    result = subprocess.run(
        [name, "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"'{name} --help' exited with code {result.returncode}.\n"
        f"stdout: {result.stdout[:500]}\n"
        f"stderr: {result.stderr[:500]}"
    )
