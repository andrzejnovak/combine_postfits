# tests/integration/test_plot_cov.py
"""Integration tests for plot_cov module.

These tests require native ROOT and are marked accordingly.
They are excluded from the default test run; use `pixi run test-root` to include them.
"""

import pytest
import shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mplhep as hep
from pathlib import Path
from matplotlib.testing.compare import compare_images
from tests.conftest import VISUAL_TOLERANCE

TESTS_DIR = Path(__file__).parent.parent
FITDIAGS = TESTS_DIR / "fitDiags"


@pytest.fixture(autouse=True)
def cleanup_plots():
    yield
    plt.close('all')


@pytest.mark.root
class TestPlotCov:
    """Test plot_cov() function."""

    def test_returns_axes(self):
        """plot_cov() should return a matplotlib Axes."""
        from combine_postfits.plot_cov import plot_cov
        ax = plot_cov(str(FITDIAGS / "fit_diag_A.root"), fit_type="fit_s")
        assert ax is not None
        assert isinstance(ax, plt.Axes)

    def test_include_filter(self):
        """plot_cov() should filter nuisances by include pattern."""
        from combine_postfits.plot_cov import plot_cov
        ax = plot_cov(
            str(FITDIAGS / "fit_diag_A.root"),
            fit_type="fit_s",
            include="r*",
        )
        assert ax is not None
        # Filtered plot should have fewer ticks than unfiltered
        labels = [t.get_text() for t in ax.get_xticklabels()]
        assert all(l.startswith("r") or l == "" for l in labels if l)

    def test_exclude_filter(self):
        """plot_cov() should exclude nuisances matching exclude pattern."""
        from combine_postfits.plot_cov import plot_cov
        ax = plot_cov(
            str(FITDIAGS / "fit_diag_A.root"),
            fit_type="fit_s",
            exclude="*mcstat*",
        )
        assert ax is not None
        labels = [t.get_text() for t in ax.get_xticklabels()]
        assert all("mcstat" not in l for l in labels)

    def test_empty_keys_raises(self):
        """plot_cov() should raise when no keys remain after filtering."""
        from combine_postfits.plot_cov import plot_cov
        with pytest.raises((AssertionError, KeyError)):
            plot_cov(
                str(FITDIAGS / "fit_diag_A.root"),
                fit_type="fit_s",
                include="nonexistent_pattern_xyz",
            )

    def test_fit_b_type(self):
        """plot_cov() should work with fit_b fit type."""
        from combine_postfits.plot_cov import plot_cov
        ax = plot_cov(str(FITDIAGS / "fit_diag_A.root"), fit_type="fit_b")
        assert ax is not None


BASELINE_DIR = TESTS_DIR / "baseline" / "cov"
OUTS_DIR = TESTS_DIR / "outs" / "cov"
FAILED_DIR = TESTS_DIR / "failed" / "cov"


@pytest.mark.root
@pytest.mark.visual
class TestPlotCovVisual:
    """Visual regression tests for plot_cov()."""

    @pytest.fixture(autouse=True)
    def setup_dirs(self):
        """Ensure output and failed directories exist."""
        OUTS_DIR.mkdir(parents=True, exist_ok=True)
        FAILED_DIR.mkdir(parents=True, exist_ok=True)
        yield
        plt.close("all")

    def test_cov_visual(self):
        """Visual regression: covariance matrix plot should match baseline."""
        from combine_postfits.plot_cov import plot_cov

        hep.style.use("CMS")
        ax = plot_cov(
            str(FITDIAGS / "fit_diag_A.root"),
            fit_type="fit_s",
            include=["r", "z", "tqq*", "tf2016_MCtempl*", "tf2016_dataResidual*"],
            exclude=None,
        )
        fig = ax.figure
        hep.cms.label(ax=ax, data=False, label="Private Work")

        output = OUTS_DIR / "cov_A_fit_s.png"
        fig.savefig(str(output), dpi=100, bbox_inches="tight")

        baseline = BASELINE_DIR / "cov_A_fit_s.png"
        assert baseline.exists(), f"Baseline missing: {baseline}"

        diff = compare_images(
            str(baseline), str(output), tol=VISUAL_TOLERANCE, in_decorator=True
        )
        if diff is not None:
            # Copy failed output for debugging
            shutil.copy2(str(output), str(FAILED_DIR / "cov_A_fit_s.png"))
            pytest.fail(f"Visual mismatch: {diff}")


@pytest.mark.root
class TestCovCLI:
    """CLI-level tests for combine_postfits_cov binary."""

    def test_cli_produces_output(self, tmp_path):
        """combine_postfits_cov should produce a PNG file."""
        import subprocess, sys
        cli = str(Path(sys.executable).parent / "combine_postfits_cov")
        result = subprocess.run(
            [cli, "-i", str(FITDIAGS / "fit_diag_A.root"),
             "-o", str(tmp_path / "cov_out"), "--data",
             "--fit", "fit_s", "--dpi", "72"],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert (tmp_path / "cov_out").exists()

    def test_cli_include_filter(self, tmp_path):
        """combine_postfits_cov --include should filter nuisances."""
        import subprocess, sys
        cli = str(Path(sys.executable).parent / "combine_postfits_cov")
        result = subprocess.run(
            [cli, "-i", str(FITDIAGS / "fit_diag_A.root"),
             "-o", str(tmp_path / "cov_out"), "--MC",
             "--fit", "fit_s", "--dpi", "72",
             "--include", "r,z"],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_cli_exclude_filter(self, tmp_path):
        """combine_postfits_cov --exclude should exclude nuisances."""
        import subprocess, sys
        cli = str(Path(sys.executable).parent / "combine_postfits_cov")
        result = subprocess.run(
            [cli, "-i", str(FITDIAGS / "fit_diag_A.root"),
             "-o", str(tmp_path / "cov_out"), "--MC",
             "--fit", "fit_s", "--dpi", "72",
             "--exclude", "*mcstat*,qcdparam*"],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"


