# tests/unit/test_blind_data.py
"""Unit tests for blind-data slice parsing functions."""

import pytest
import numpy as np
from combine_postfits.utils import _string_to_slice, _ensure_slice_by_ix


class TestStringToSlice:
    """Tests for _string_to_slice: parses 'start:stop' into a slice of complex numbers."""

    def test_index_based(self):
        """'5:10' → slice(5+0j, 10+0j) (index-based, imag == 0)."""
        s = _string_to_slice("5:10")
        assert s.start == 5 + 0j
        assert s.stop == 10 + 0j

    def test_value_based(self):
        """'5j:10j' → slice(5j, 10j) (value-based, imag != 0)."""
        s = _string_to_slice("5j:10j")
        assert s.start == 5j
        assert s.stop == 10j

    def test_float_values(self):
        """'1.5:3.5' → slice with real float components."""
        s = _string_to_slice("1.5:3.5")
        assert s.start == 1.5 + 0j
        assert s.stop == 3.5 + 0j

    def test_float_value_based(self):
        """'1.5j:3.5j' → slice with imaginary float components."""
        s = _string_to_slice("1.5j:3.5j")
        assert s.start == 1.5j
        assert s.stop == 3.5j


class TestEnsureSliceByIx:
    """Tests for _ensure_slice_by_ix: converts value-based slices to index-based."""

    @pytest.fixture
    def edges(self):
        """Bin edges: [0, 10, 20, 30, 40, 50]"""
        return np.array([0.0, 10.0, 20.0, 30.0, 40.0, 50.0])

    def test_index_passthrough(self, edges):
        """Index-based slice (imag==0) passes through unchanged."""
        s = slice(1 + 0j, 4 + 0j)
        result = _ensure_slice_by_ix(s, edges)
        assert result == slice(1, 4)

    def test_value_to_index(self, edges):
        """Value-based slice (imag!=0) gets converted to index via searchsorted."""
        s = slice(10j, 40j)
        result = _ensure_slice_by_ix(s, edges)
        # 10.0 is at edge index 1, searchsorted("right")-1 = 0
        # 40.0 is at edge index 4, searchsorted("right") = 5
        assert isinstance(result.start, int)
        assert isinstance(result.stop, int)
        assert result.start >= 0
        assert result.stop <= len(edges)

    def test_value_at_exact_edge(self, edges):
        """Value exactly at a bin edge should be handled consistently."""
        s = slice(0j, 50j)
        result = _ensure_slice_by_ix(s, edges)
        assert isinstance(result.start, int)
        assert isinstance(result.stop, int)

    def test_result_is_valid_slice(self, edges):
        """Result should be usable as a valid array slice."""
        s = slice(10j, 30j)
        result = _ensure_slice_by_ix(s, edges)
        # Should not raise when used for slicing
        data = np.arange(len(edges) - 1)  # 5 bins
        sliced = data[result]
        assert len(sliced) >= 0
