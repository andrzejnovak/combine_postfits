# tests/integration/test_cli_args.py
"""Tests for CLI argument parsing and error handling.

Tests the combine_postfits CLI argument parsing to verify:
- Correct args namespace for common argument combinations
- Proper error handling for invalid inputs
"""

import sys
from collections import namedtuple
from pathlib import Path
from unittest.mock import patch

import matplotlib.pyplot as plt
import pytest

from combine_postfits import make_plots

TESTS_DIR = Path(__file__).parent.parent
FITDIAGS = TESTS_DIR / "fitDiags"


# Mimic subprocess.CompletedProcess
CompletedProcess = namedtuple("CompletedProcess", ["returncode", "stdout", "stderr"])


class TestCLIArgParsing:
    """Test CLI argument parsing produces correct behavior."""

    def run_cli(self, args, capsys):
        """Run the CLI in-process."""
        # reset argv for the test
        with patch.object(sys, "argv", args):
            try:
                make_plots.main()
                returncode = 0
            except SystemExit as e:
                returncode = e.code if e.code is not None else 0
            except Exception:
                returncode = 1
            finally:
                plt.close("all")

        captured = capsys.readouterr()
        return CompletedProcess(returncode, captured.out, captured.err)

    def test_minimal_mc(self, tmp_path, capsys):
        """Minimal MC invocation should produce output."""
        result = self.run_cli(
            [
                "combine_postfits",
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
                "--cats",
                "ptbin0passhighbvl",
            ],
            capsys,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert (tmp_path / "out" / "prefit").exists()

    def test_fit_type_choices(self, tmp_path, capsys):
        """--fit should accept prefit, fit_s, fit_b, all."""
        for fit in ["prefit", "fit_s", "fit_b"]:
            result = self.run_cli(
                [
                    "combine_postfits",
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
                    "--cats",
                    "ptbin0passhighbvl",
                ],
                capsys,
            )
            assert result.returncode == 0, f"fit={fit} failed: {result.stderr}"

    def test_format_choices(self, tmp_path, capsys):
        """--format should accept png, pdf, both."""
        for fmt in ["png", "pdf"]:
            result = self.run_cli(
                [
                    "combine_postfits",
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
                    "--cats",
                    "ptbin0passhighbvl",
                ],
                capsys,
            )
            assert result.returncode == 0, f"format={fmt} failed: {result.stderr}"

    def test_cats_list(self, tmp_path, capsys):
        """--cats with comma-separated list should filter categories."""
        result = self.run_cli(
            [
                "combine_postfits",
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
            capsys,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_cats_glob(self, tmp_path, capsys):
        """--cats with glob pattern should match multiple categories."""
        result = self.run_cli(
            [
                "combine_postfits",
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
            capsys,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_styling_options(self, tmp_path, capsys):
        """Styling options (cmslabel, year, lumi, dpi) should be accepted."""
        result = self.run_cli(
            [
                "combine_postfits",
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
                "--cats",
                "ptbin0passhighbvl",
            ],
            capsys,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_blind_category(self, tmp_path, capsys):
        """--blind should suppress data in matched categories."""
        result = self.run_cli(
            [
                "combine_postfits",
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
            capsys,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_blind_data_range(self, tmp_path, capsys):
        """--blind-data should accept category:slice format."""
        result = self.run_cli(
            [
                "combine_postfits",
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
            capsys,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_debug_flags(self, tmp_path, capsys):
        """--chi2, --residuals, --verbose should be accepted."""
        result = self.run_cli(
            [
                "combine_postfits",
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
            capsys,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"


class TestCLIErrorPaths:
    """Test CLI handles error conditions gracefully."""

    def run_cli(self, args, capsys):
        """Run the CLI in-process."""
        # reset argv for the test
        with patch.object(sys, "argv", args):
            with pytest.raises(SystemExit) as excinfo:
                make_plots.main()
            returncode = excinfo.value.code
        captured = capsys.readouterr()
        return CompletedProcess(returncode, captured.out, captured.err)

    def test_missing_data_mc_flag(self, capsys):
        """CLI should fail without --data or --MC."""
        result = self.run_cli(
            ["combine_postfits", "-i", str(FITDIAGS / "fit_diag_B.root"), "--noroot"],
            capsys,
        )
        assert result.returncode != 0

    def test_invalid_fit_type(self, capsys):
        """CLI should reject invalid --fit values."""
        result = self.run_cli(
            [
                "combine_postfits",
                "-i",
                str(FITDIAGS / "fit_diag_B.root"),
                "--MC",
                "--fit",
                "invalid_fit",
                "--noroot",
            ],
            capsys,
        )
        assert result.returncode != 0

    def test_invalid_format(self, capsys):
        """CLI should reject invalid --format values."""
        result = self.run_cli(
            [
                "combine_postfits",
                "-i",
                str(FITDIAGS / "fit_diag_B.root"),
                "--MC",
                "-f",
                "svg",
                "--noroot",
            ],
            capsys,
        )
        assert result.returncode != 0

    def test_nonexistent_input(self, tmp_path, capsys):
        """CLI should fail with nonexistent input file."""
        with patch.object(
            sys,
            "argv",
            [
                "combine_postfits",
                "-i",
                str(tmp_path / "nonexistent.root"),
                "-o",
                str(tmp_path / "out"),
                "--MC",
                "--noroot",
                "--fit",
                "prefit",
            ],
        ):
            # uproot.open will raise FileNotFoundError (or OSError)
            with pytest.raises(Exception):
                make_plots.main()

    def test_no_matching_cats(self, tmp_path, capsys):
        """CLI should fail when --cats matches no categories."""
        # This raises an AssertionError in main.py: assert len(channels) != 0
        with patch.object(
            sys,
            "argv",
            [
                "combine_postfits",
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
        ):
            with pytest.raises(AssertionError):
                make_plots.main()
