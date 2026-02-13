# tests/unit/test_root_utils.py
"""Unit tests for ROOT-dependent utility functions.

These tests require native ROOT and are excluded from the default test run.
Run with `pixi run test-root` to include them.
"""

import pytest

FITDIAG_PATH = "tests/fitDiags/fit_diag_A.root"


@pytest.mark.root
class TestGetFitVal:
    """Tests for get_fit_val() ROOT parameter extraction."""

    @pytest.fixture
    def fitdiag(self):
        """Open the ROOT fitDiagnostics file."""
        import ROOT as r

        rf = r.TFile.Open(FITDIAG_PATH)
        yield rf
        rf.Close()

    def test_returns_float(self, fitdiag):
        """get_fit_val should return a float for existing parameter."""
        from combine_postfits.utils import get_fit_val

        val = get_fit_val(fitdiag, "r", fittype="fit_s")
        assert isinstance(val, float)

    def test_missing_param_returns_substitute(self, fitdiag):
        """get_fit_val should return substitute for nonexistent parameter."""
        from combine_postfits.utils import get_fit_val

        val = get_fit_val(fitdiag, "nonexistent_param_xyz", fittype="fit_s", substitute=42.0)
        assert val == 42.0

    def test_none_fitdiag_returns_substitute(self):
        """get_fit_val with None fitDiag should return substitute."""
        from combine_postfits.utils import get_fit_val

        val = get_fit_val(None, "r", substitute=1.0)
        assert val == 1.0


@pytest.mark.root
class TestGetFitUnc:
    """Tests for get_fit_unc() ROOT uncertainty extraction."""

    @pytest.fixture
    def fitdiag(self):
        """Open the ROOT fitDiagnostics file."""
        import ROOT as r

        rf = r.TFile.Open(FITDIAG_PATH)
        yield rf
        rf.Close()

    def test_returns_tuple(self, fitdiag):
        """get_fit_unc should return a 2-tuple for existing parameter."""
        from combine_postfits.utils import get_fit_unc

        unc = get_fit_unc(fitdiag, "r", fittype="fit_s")
        assert isinstance(unc, tuple)
        assert len(unc) == 2

    def test_uncertainties_are_numeric(self, fitdiag):
        """get_fit_unc should return numeric values."""
        from combine_postfits.utils import get_fit_unc

        lo, hi = get_fit_unc(fitdiag, "r", fittype="fit_s")
        assert isinstance(lo, float)
        assert isinstance(hi, float)

    def test_missing_param_returns_substitute(self, fitdiag):
        """get_fit_unc should return substitute for nonexistent parameter."""
        from combine_postfits.utils import get_fit_unc

        unc = get_fit_unc(fitdiag, "nonexistent_param_xyz", fittype="fit_s", substitute=(0, 0))
        assert unc == (0, 0)

    def test_none_fitdiag_returns_substitute(self):
        """get_fit_unc with None fitDiag should return substitute."""
        from combine_postfits.utils import get_fit_unc

        unc = get_fit_unc(None, "r", substitute=(0, 0))
        assert unc == (0, 0)
