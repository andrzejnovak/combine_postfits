"""
Test case definitions for combine_postfits.

Each test case represents a CLI invocation pattern for visual regression testing.
Cases are assigned to tiers: quick < standard < full.

Tier model:
    quick    - Single smoke test (plots_B)
    standard - Handpicked cases (B, A, C, D base)
    full     - All cases including *_all variants
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class VisualTestCase:
    """A visual test case configuration."""
    name: str
    fitdiag: str                    # Input ROOT file
    style: Optional[str]            # Style YAML (None = auto-style)
    cli_args: List[str]             # CLI arguments
    description: str                # What this tests
    tier: str                       # "quick" | "standard" | "full"

    def to_cli_command(self, output_dir: str = "outs") -> str:
        """Generate CLI command for manual execution."""
        base = f"combine_postfits -i fitDiags/{self.fitdiag} -o {output_dir}/{self.name}"
        if self.style:
            base += f" --style styles/{self.style}"
        return f"{base} {' '.join(self.cli_args)}"


# ==========================================================================
# Test Cases
# ==========================================================================

TEST_CASES = {
    # ----- QUICK: Single smoke test -----
    "plots_B": VisualTestCase(
        name="plots_B",
        fitdiag="fit_diag_B.root",
        style="style_B.yml",
        tier="quick",
        cli_args=[
            "--toys",
            "--xlabel", "Jet $m_{SD}$",
            "--sigs", "b150,m150",
            "--project-signals", "2,2",
            "--rmap", "m150:r_q,b150:r_b",
            "--bkgs", "top,vlep,wqq,zqq,zbb,hbb",
            "--onto", "2017_qcd",
            "--cats", "fail:ptbin*fail;passlow:ptbin*high*;passhigh:ptbin*passlow*",
        ],
        description="Basic toys data with signal projection",
    ),

    # ----- STANDARD: Handpicked cases -----
    "plots_A": VisualTestCase(
        name="plots_A",
        fitdiag="fit_diag_A.root",
        style="style_A.yml",
        tier="standard",
        cli_args=[
            "--data", "--unblind",
            "--sigs", "hcc,zcc",
            "--onto", "qcd",
            "--rmap", "zcc:z,hcc:r",
            "--cats", "pass:ptbin*pass2016;fail:ptbin*fail*;muCRpass:muonCRpass2016;muCRfail:muonCRfail2016",
            "--bkgs", "top,other,wqq,wcq,zqq,zbb,hbb",
            "--project-signal", "50,0",
        ],
        description="Real data with H/Z signals, unblinding",
    ),

    "plots_C": VisualTestCase(
        name="plots_C",
        fitdiag="fit_diag_C.root",
        style="style_C.yml",
        tier="standard",
        cli_args=[
            "--toys",
            "--chi2", "--residuals",
            "--xlabel", "Jet $m_{reg}$",
        ],
        description="Chi-squared and residual plots",
    ),

    "plots_D": VisualTestCase(
        name="plots_D",
        fitdiag="fit_diag_D.root",
        style="style_D.yml",
        tier="standard",
        cli_args=[
            "--MC",
            "--onto", "qcd",
            "--sigs", "VH",
            "--bkgs", "qcd,top,Wjets,Zjets,VV,H",
            "--rmap", "VH:rVH",
            "--project-signals", "3",
            "--xlabel", "Jet $m_{SD}$",
            "--vv",
        ],
        description="VH analysis with custom signals",
    ),

    # ----- FULL: All variants -----
    "plots_B_all": VisualTestCase(
        name="plots_B_all",
        fitdiag="fit_diag_B.root",
        style=None,
        tier="full",
        cli_args=["--MC"],
        description="All B categories, auto-styling",
    ),

    "plots_A_all": VisualTestCase(
        name="plots_A_all",
        fitdiag="fit_diag_A.root",
        style=None,
        tier="full",
        cli_args=[
            "--data", "--unblind",
            "--chi2", "--residuals",
        ],
        description="All A categories with chi2/residuals",
    ),

    "plots_Abig": VisualTestCase(
        name="plots_Abig",
        fitdiag="fit_diag_Abig.root",
        style="style_A.yml",
        tier="full",
        cli_args=[
            "--data", "--unblind",
            "--sigs", "hcc,zcc",
            "--onto", "qcd",
            "--rmap", "zcc:z,hcc:r",
            "--cats", "pass16:ptbin*pass2016;fail16:ptbin*fail2016;pass17:ptbin*pass2017;fail17:ptbin*fail2017;pass18:ptbin*pass2018;fail18:ptbin*fail2018;pass:ptbin*pass*;fail:ptbin*fail*;muCRpass16:muonCRpass2016;muCRfail16:muonCRfail2016;muCRpass17:muonCRpass2017;muCRfail17:muonCRfail2017;muCRpass18:muonCRpass2018;muCRfail18:muonCRfail2018",
            "--bkgs", "top,other,wqq,wcq,zqq,zbb,hbb",
            "--project-signal", "50,0",
        ],
        description="Multi-year analysis (2016/17/18)",
    ),

    "plots_Abig_all": VisualTestCase(
        name="plots_Abig_all",
        fitdiag="fit_diag_Abig.root",
        style=None,
        tier="full",
        cli_args=["--data", "--unblind"],
        description="All Abig categories (stress test)",
    ),

    "plots_C_all": VisualTestCase(
        name="plots_C_all",
        fitdiag="fit_diag_C.root",
        style=None,
        tier="full",
        cli_args=[
            "--MC",
            "--chi2", "--residuals",
        ],
        description="All C categories",
    ),

    "plots_D_all": VisualTestCase(
        name="plots_D_all",
        fitdiag="fit_diag_D.root",
        style=None,
        tier="full",
        cli_args=["--MC"],
        description="All D categories",
    ),
}
