# tests/conftest.py
"""Shared pytest fixtures for combine_postfits tests."""

import pytest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import uproot

# Zero tolerance for publication-quality visual regression.
# DO NOT CHANGE without team review.
VISUAL_TOLERANCE = 0

TESTS_DIR = Path(__file__).parent
FITDIAGS = TESTS_DIR / "fitDiags"


@pytest.fixture(scope="session")
def fitdiag_A():
    """fitDiagnostics file for test case A"""
    return uproot.open(FITDIAGS / "fit_diag_A.root")


@pytest.fixture(scope="session")
def fitdiag_Abig():
    """fitDiagnostics file for test case Abig"""
    return uproot.open(FITDIAGS / "fit_diag_Abig.root")


@pytest.fixture(scope="session")
def fitdiag_B():
    """fitDiagnostics file for test case B"""
    return uproot.open(FITDIAGS / "fit_diag_B.root")


@pytest.fixture(scope="session")
def fitdiag_C():
    """fitDiagnostics file for test case C"""
    return uproot.open(FITDIAGS / "fit_diag_C.root")


@pytest.fixture(scope="session")
def fitdiag_D():
    """fitDiagnostics file for test case D"""
    return uproot.open(FITDIAGS / "fit_diag_D.root")


@pytest.fixture(autouse=True)
def reset_matplotlib():
    """Reset matplotlib state between tests to prevent leakage"""
    yield
    plt.close('all')


@pytest.fixture
def base_style():
    """Minimal valid style dict for testing"""
    return {
        "data": {"label": "Data", "color": "black", "hatch": None},
        "total_signal": {"label": "Signal", "color": "red", "hatch": None},
        "total_background": {"label": "Background", "color": "gray", "hatch": None},
        "total": {"label": "Total", "color": "black", "hatch": None},
    }


@pytest.fixture
def style_A():
    """Style dict matching test case A"""
    return {
        "data": {"label": "Data", "color": "black", "hatch": None},
        "total_signal": {"label": "Signal", "color": "red", "hatch": None},
        "hcc": {"label": r"$H(c\bar{c})$", "color": "#3f90da", "hatch": None},
        "zcc": {"label": r"$Z(c\bar{c})$", "color": "#ffa90e", "hatch": None},
        "qcd": {"label": "QCD", "color": "#bd1f01", "hatch": "///"},
        "zbb": {"label": r"$Z(b\bar{b})$", "color": "#94a4a2", "hatch": None},
        "hbb": {"label": r"$H(b\bar{b})$", "color": "#832db6", "hatch": None},
        "zqq": {"label": r"$Z(q\bar{q})$", "color": "#a96b59", "hatch": None},
        "wcq": {"label": r"$W(cq)$", "color": "#e76300", "hatch": None},
        "wqq": {"label": r"$W(q\bar{q})$", "color": "#b9ac70", "hatch": None},
        "other": {"label": "Other", "color": "#717581", "hatch": None},
        "top": {"label": "Top", "color": "#92dadd", "hatch": None},
        "total_background": {"label": "Background", "color": "gray", "hatch": None},
        "total": {"label": "Total", "color": "black", "hatch": None},
    }
