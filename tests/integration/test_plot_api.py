# tests/integration/test_plot_api.py
"""Integration tests for plot_postfits.plot() API behavior.

These tests verify the plot() function returns correct values and behaves
as expected without performing image comparisons.
"""

import pytest
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from combine_postfits.plot_postfits import plot

TESTS_DIR = Path(__file__).parent.parent


@pytest.fixture(autouse=True)
def cleanup_plots():
    """Reset matplotlib state between tests to prevent leakage"""
    yield
    plt.close('all')


@pytest.fixture
def minimal_style(fitdiag_A):
    """Create a minimal style dict with just the histograms needed for basic tests."""
    # Use ptbin0pass2016 category which has qcd, hcc, zcc
    channels = [fitdiag_A["shapes_prefit/ptbin0pass2016"]]
    hist_keys = [
        k.split(";")[0]
        for k in list(set(sum([c.keys() for c in channels], [])))
        if "data" not in k and "covar" not in k
    ]
    # Build minimal style with all required keys
    style = {
        "data": {"label": "Data", "color": "black", "hatch": None},
    }
    for key in hist_keys:
        if key not in style:
            style[key] = {"label": key, "color": None, "hatch": None}
    return style


class TestPlotReturns:
    """Test plot() return values and types."""

    def test_returns_figure_and_axes(self, fitdiag_A, minimal_style):
        """plot() should return figure and axes tuple."""
        fig, (ax, rax) = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            style=minimal_style,
        )
        assert fig is not None
        assert ax is not None
        assert rax is not None
        assert isinstance(fig, plt.Figure)

    def test_returns_none_for_empty_channels(self, fitdiag_A, minimal_style):
        """plot() should return None when given empty category list."""
        result = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=[],
            style=minimal_style,
        )
        assert result == (None, (None, None))

    def test_returns_tuple_with_two_elements(self, fitdiag_A, minimal_style):
        """plot() should always return a 2-tuple."""
        result = plot(fitdiag_A, fit_type="prefit", cats=["ptbin0pass2016"], style=minimal_style)
        assert isinstance(result, tuple)
        assert len(result) == 2
        fig, axes = result
        assert isinstance(axes, tuple)


class TestPlotOptions:
    """Test various plot configuration options."""

    @pytest.mark.parametrize("fit_type", ["prefit", "fit_s"])
    def test_fit_types(self, fitdiag_A, minimal_style, fit_type):
        """plot() should handle different fit types."""
        fig, _ = plot(
            fitdiag_A,
            fit_type=fit_type,
            cats=["ptbin0pass2016"],
            style=minimal_style,
        )
        assert fig is not None

    def test_blind_mode(self, fitdiag_A, minimal_style):
        """In blind mode, plot() should still work."""
        fig, _ = plot(
            fitdiag_A,
            fit_type="prefit",
            blind=True,
            cats=["ptbin0pass2016"],
            style=minimal_style,
        )
        assert fig is not None

    def test_category_selection_single(self, fitdiag_A, minimal_style):
        """plot() should work with single category."""
        fig, _ = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            style=minimal_style,
        )
        assert fig is not None

    def test_category_selection_multiple(self, fitdiag_A, minimal_style):
        """plot() should work with multiple categories."""
        fig, _ = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016", "ptbin1pass2016"],
            style=minimal_style,
        )
        assert fig is not None


class TestPlotContent:
    """Test the content of generated plots."""

    def test_axis_labels_set(self, fitdiag_A, minimal_style):
        """Axes should have labels set."""
        fig, (ax, rax) = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            style=minimal_style,
        )
        # x-label should be on ratio axis
        assert rax.get_xlabel() != ""
        # y-label should be on main axis
        assert ax.get_ylabel() != ""

    def test_axis_limits_set(self, fitdiag_A, minimal_style):
        """Axes should have limits set."""
        fig, (ax, rax) = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            style=minimal_style,
        )
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        # Should have finite limits
        assert xlim[0] < xlim[1]
        assert ylim[0] < ylim[1]


class TestPlotSignals:
    """Test signal-related options."""

    def test_custom_signals(self, fitdiag_A, minimal_style):
        """plot() should accept custom signal list."""
        fig, _ = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            sigs=["hcc"],
            style=minimal_style,
        )
        assert fig is not None


class TestPlotBackgrounds:
    """Test background-related options."""

    def test_remove_tiny_threshold(self, fitdiag_A, minimal_style):
        """plot() should handle remove_tiny option."""
        fig, _ = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            remove_tiny=10,
            style=minimal_style,
        )
        assert fig is not None

    def test_remove_tiny_percentage(self, fitdiag_A, minimal_style):
        """plot() should handle remove_tiny with percentage."""
        fig, _ = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            remove_tiny="5%",
            style=minimal_style,
        )
        assert fig is not None


class TestPlotChi2:
    """Test chi2 calculation and display."""

    def test_chi2_option(self, fitdiag_A, minimal_style):
        """plot() should calculate chi2 when requested."""
        fig, (ax, rax) = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            chi2=True,
            style=minimal_style,
        )
        # Chi2 annotation should be present in ratio axis
        assert len(rax.texts) > 0 or len(rax.artists) > 0

    def test_chi2_nocorr_option(self, fitdiag_A, minimal_style):
        """plot() should calculate naive chi2 when requested."""
        fig, (ax, rax) = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            chi2_nocorr=True,
            style=minimal_style,
        )
        # Chi2 annotation should be present
        assert len(rax.texts) > 0 or len(rax.artists) > 0


class TestPlotErrors:
    """Test error handling in plot()."""

    def test_invalid_category_raises(self, fitdiag_A):
        """plot() should raise error for invalid category."""
        with pytest.raises(Exception):  # uproot.KeyInFileError
            plot(
                fitdiag_A,
                fit_type="prefit",
                cats=["nonexistent_category"],
                style={},
            )

    def test_too_many_signals_raises(self, fitdiag_A, minimal_style):
        """plot() should raise error for more than 2 signals."""
        with pytest.raises(ValueError, match="insane|More than 2"):
            plot(
                fitdiag_A,
                fit_type="prefit",
                cats=["ptbin0pass2016"],
                sigs=["sig1", "sig2", "sig3"],
                style=minimal_style,
            )


class TestPlotWithStyle:
    """Test plotting with explicit style dict."""

    def test_with_minimal_style(self, fitdiag_A, minimal_style):
        """plot() should work with minimal style dict."""
        fig, _ = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            style=minimal_style,
        )
        assert fig is not None

    def test_onto_option(self, fitdiag_A, minimal_style):
        """plot() should handle onto option for stacking."""
        fig, _ = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            onto="qcd",
            style=minimal_style,
        )
        assert fig is not None

    def test_custom_backgrounds(self, fitdiag_A, minimal_style):
        """plot() should accept custom background list."""
        fig, _ = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            bkgs=["hcc", "qcd"],
            style=minimal_style,
        )
        assert fig is not None

    def test_with_fitdiag_root(self, fitdiag_A, minimal_style):
        """plot() should work with fitDiag_root parameter."""
        FITDIAGS = TESTS_DIR / "fitDiags"
        fig, _ = plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            fitDiag_root=str(FITDIAGS / "fit_diag_A.root"),
            style=minimal_style,
        )
        assert fig is not None
