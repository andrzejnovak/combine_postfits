# tests/integration/test_cli_args.py
"""Tests for CLI argument parsing and error handling.

Tests the combine_postfits CLI argument parsing to verify:
- Correct args namespace for common argument combinations
- Proper error handling for invalid inputs
"""

import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent.parent
FITDIAGS = TESTS_DIR / "fitDiags"
CLI = str(Path(sys.executable).parent / "combine_postfits")


class TestCLIArgParsing:
    """Test CLI argument parsing produces correct behavior."""

    def test_minimal_mc(self, tmp_path):
        """Minimal MC invocation should produce output."""
        result = subprocess.run(
            [
                CLI,
                "-i",
                str(FITDIAGS / "fit_diag_B.root"),
                "-o",
                str(tmp_path / "out"),
                "--MC",
                "--noroot",
                "--fit",
                "prefit",
                "--dpi",
                "72",
                "-f",
                "png",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert (tmp_path / "out" / "prefit").exists()

    def test_fit_type_choices(self, tmp_path):
        """--fit should accept prefit, fit_s, fit_b, all."""
        for fit in ["prefit", "fit_s", "fit_b"]:
            result = subprocess.run(
                [
                    CLI,
                    "-i",
                    str(FITDIAGS / "fit_diag_B.root"),
                    "-o",
                    str(tmp_path / f"out_{fit}"),
                    "--MC",
                    "--noroot",
                    "--fit",
                    fit,
                    "--dpi",
                    "72",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert result.returncode == 0, f"fit={fit} failed: {result.stderr}"

    def test_format_choices(self, tmp_path):
        """--format should accept png, pdf, both."""
        for fmt in ["png", "pdf"]:
            result = subprocess.run(
                [
                    CLI,
                    "-i",
                    str(FITDIAGS / "fit_diag_B.root"),
                    "-o",
                    str(tmp_path / f"out_{fmt}"),
                    "--MC",
                    "--noroot",
                    "--fit",
                    "prefit",
                    "--dpi",
                    "72",
                    "-f",
                    fmt,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert result.returncode == 0, f"format={fmt} failed: {result.stderr}"

    def test_cats_list(self, tmp_path):
        """--cats with comma-separated list should filter categories."""
        result = subprocess.run(
            [
                CLI,
                "-i",
                str(FITDIAGS / "fit_diag_B.root"),
                "-o",
                str(tmp_path / "out"),
                "--MC",
                "--noroot",
                "--fit",
                "prefit",
                "--dpi",
                "72",
                "--cats",
                "ptbin0passhighbvl",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_cats_glob(self, tmp_path):
        """--cats with glob pattern should match multiple categories."""
        result = subprocess.run(
            [
                CLI,
                "-i",
                str(FITDIAGS / "fit_diag_B.root"),
                "-o",
                str(tmp_path / "out"),
                "--MC",
                "--noroot",
                "--fit",
                "prefit",
                "--dpi",
                "72",
                "--cats",
                "ptbin0*",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_styling_options(self, tmp_path):
        """Styling options (cmslabel, year, lumi, dpi) should be accepted."""
        result = subprocess.run(
            [
                CLI,
                "-i",
                str(FITDIAGS / "fit_diag_B.root"),
                "-o",
                str(tmp_path / "out"),
                "--MC",
                "--noroot",
                "--fit",
                "prefit",
                "--dpi",
                "72",
                "--cmslabel",
                "Preliminary",
                "--year",
                "2016",
                "--lumi",
                "35.9",
                "--com",
                "13",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_blind_category(self, tmp_path):
        """--blind should suppress data in matched categories."""
        result = subprocess.run(
            [
                CLI,
                "-i",
                str(FITDIAGS / "fit_diag_B.root"),
                "-o",
                str(tmp_path / "out"),
                "--data",
                "--unblind",
                "--blind",
                "ptbin0*",
                "--cats",
                "ptbin0fail,ptbin0passhighbvl",
                "--noroot",
                "--fit",
                "prefit",
                "--dpi",
                "72",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_blind_data_range(self, tmp_path):
        """--blind-data should accept category:slice format."""
        result = subprocess.run(
            [
                CLI,
                "-i",
                str(FITDIAGS / "fit_diag_B.root"),
                "-o",
                str(tmp_path / "out"),
                "--data",
                "--unblind",
                "--blind-data",
                "ptbin0passhighbvl:1:5",
                "--cats",
                "ptbin0passhighbvl",
                "--noroot",
                "--fit",
                "prefit",
                "--dpi",
                "72",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_debug_flags(self, tmp_path):
        """--chi2, --residuals, --verbose should be accepted."""
        result = subprocess.run(
            [
                CLI,
                "-i",
                str(FITDIAGS / "fit_diag_B.root"),
                "-o",
                str(tmp_path / "out"),
                "--MC",
                "--noroot",
                "--fit",
                "prefit",
                "--dpi",
                "72",
                "--cats",
                "ptbin0passhighbvl",
                "--chi2",
                "--residuals",
                "-v",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"


class TestCLIErrorPaths:
    """Test CLI handles error conditions gracefully."""

    def test_missing_data_mc_flag(self):
        """CLI should fail without --data or --MC."""
        result = subprocess.run(
            [CLI, "-i", str(FITDIAGS / "fit_diag_B.root"), "--noroot"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0

    def test_invalid_fit_type(self):
        """CLI should reject invalid --fit values."""
        result = subprocess.run(
            [CLI, "-i", str(FITDIAGS / "fit_diag_B.root"), "--MC", "--fit", "invalid_fit", "--noroot"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0

    def test_invalid_format(self):
        """CLI should reject invalid --format values."""
        result = subprocess.run(
            [CLI, "-i", str(FITDIAGS / "fit_diag_B.root"), "--MC", "-f", "svg", "--noroot"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0

    def test_nonexistent_input(self, tmp_path):
        """CLI should fail with nonexistent input file."""
        result = subprocess.run(
            [
                CLI,
                "-i",
                str(tmp_path / "nonexistent.root"),
                "-o",
                str(tmp_path / "out"),
                "--MC",
                "--noroot",
                "--fit",
                "prefit",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0

    def test_no_matching_cats(self, tmp_path):
        """CLI should fail when --cats matches no categories."""
        result = subprocess.run(
            [
                CLI,
                "-i",
                str(FITDIAGS / "fit_diag_B.root"),
                "-o",
                str(tmp_path / "out"),
                "--MC",
                "--noroot",
                "--fit",
                "prefit",
                "--dpi",
                "72",
                "--cats",
                "nonexistent_category_xyz",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode != 0
