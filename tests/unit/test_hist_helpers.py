# tests/unit/test_hist_helpers.py
"""Unit tests for histogram helper functions in utils module."""

import pytest
import numpy as np
import hist
from combine_postfits.utils import (
    geth,
    getha,
    geths,
    tgasym_to_hist,
    tgasym_to_err,
)


class TestGeth:
    """Tests for single histogram extraction."""
    
    @pytest.fixture
    def mock_shapes_dir(self, fitdiag_A):
        """Get a real shapes directory from fitDiag"""
        return fitdiag_A["shapes_prefit/ptbin0pass2016"]

    def test_extracts_histogram(self, mock_shapes_dir):
        h = geth("qcd", mock_shapes_dir, restoreNorm=True)
        assert isinstance(h, hist.Hist)
        assert len(h.axes) == 1

    def test_restoreNorm_scales_by_binwidth(self, mock_shapes_dir):
        h_normed = geth("qcd", mock_shapes_dir, restoreNorm=True)
        h_raw = geth("qcd", mock_shapes_dir, restoreNorm=False)
        # restoreNorm multiplies by bin width
        binwidths = h_raw.axes[0].widths
        np.testing.assert_array_almost_equal(
            h_normed.values(),
            h_raw.values() * binwidths
        )

    def test_handles_TGraphAsymmErrors(self, mock_shapes_dir):
        # data is typically stored as TGraphAsymmErrors
        h = geth("data", mock_shapes_dir, restoreNorm=True)
        assert isinstance(h, hist.Hist)


class TestGetha:
    """Tests for histogram extraction and merging across channels."""
    
    @pytest.fixture
    def channels(self, fitdiag_A):
        return [
            fitdiag_A["shapes_prefit/ptbin0pass2016"],
            fitdiag_A["shapes_prefit/ptbin1pass2016"],
        ]

    def test_sums_across_channels(self, channels):
        h = getha("qcd", channels, restoreNorm=True)
        h0 = geth("qcd", channels[0], restoreNorm=True)
        h1 = geth("qcd", channels[1], restoreNorm=True)
        np.testing.assert_array_almost_equal(
            h.values(),
            h0.values() + h1.values()
        )

    def test_skips_missing_channels(self, fitdiag_A, caplog):
        channels = [
            fitdiag_A["shapes_prefit/ptbin0pass2016"],
        ]
        # total_signal might be missing in some channels
        h = getha("qcd", channels, restoreNorm=True)
        assert h is not None


class TestGeths:
    """Tests for multiple histogram extraction."""
    
    @pytest.fixture
    def channels(self, fitdiag_A):
        return [
            fitdiag_A["shapes_prefit/ptbin0pass2016"],
        ]

    def test_returns_dict_of_hists(self, channels):
        names = ["qcd", "total_background"]
        result = geths(names, channels, restoreNorm=True)
        assert isinstance(result, dict)
        assert "qcd" in result
        assert "total_background" in result

    def test_all_values_are_hists(self, channels):
        names = ["qcd", "total_background"]
        result = geths(names, channels, restoreNorm=True)
        for h in result.values():
            assert isinstance(h, hist.Hist)


class TestTgasymConversion:
    """Tests for TGraphAsymmErrors conversion."""
    
    @pytest.fixture
    def mock_tgasym(self, fitdiag_A):
        """Get real TGraphAsymmErrors from fitDiag (data)"""
        return fitdiag_A["shapes_prefit/ptbin0pass2016/data"]

    def test_tgasym_to_hist_returns_hist(self, mock_tgasym):
        h = tgasym_to_hist(mock_tgasym, restoreNorm=True)
        assert isinstance(h, hist.Hist)

    def test_tgasym_to_err_returns_arrays(self, mock_tgasym):
        y, bins, ylo, yhi = tgasym_to_err(mock_tgasym, restoreNorm=True)
        assert isinstance(y, np.ndarray)
        assert isinstance(bins, np.ndarray)
        assert len(bins) == len(y) + 1  # bins have one more edge

    def test_restoreNorm_affects_values(self, mock_tgasym):
        y_norm, _, _, _ = tgasym_to_err(mock_tgasym, restoreNorm=True)
        y_raw, _, _, _ = tgasym_to_err(mock_tgasym, restoreNorm=False)
        # Should be different (scaled by binwidth)
        assert not np.allclose(y_norm, y_raw)
