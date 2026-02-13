#!/bin/bash
#
# CLI USAGE EXAMPLES FOR combine_postfits
#
# This file contains real, runnable examples of combine_postfits CLI usage.
# Each example corresponds to a visual regression test case.
#
# Usage:
#   ./examples.sh B          # Run single case
#   ./examples.sh all        # Run all cases
#   ./examples.sh quick      # Run quick smoke test
#   ./examples.sh standard   # Run standard test matrix
#
# ⚠️  HAND-MAINTAINED - edit directly as needed
#

set -e  # Exit on error

cd "$(dirname "$0")"  # Run from tests/ directory

# Common options
DPI=100
PROCESSES=20
OPTS="--noroot"

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

run_case() {
    local name=$1
    local cmd=$2
    echo -e "${BLUE}Running: ${name}${NC}"
    echo -e "${GREEN}${cmd}${NC}"
    eval "$cmd"
    echo ""
}

# ============================================================================
# QUICK TEST (default for development)
# Single representative case: ~6 images, <10 seconds
# ============================================================================

if [ "$1" = "B" ] || [ "$1" = "quick" ] || [ "$1" = "all" ]; then
    echo "=== PLOTS_B: Basic plotting with toys data, signal projection, and category grouping ==="
    echo "Features: toys, projection"
    echo ""

    run_case "plots_B" \
        'combine_postfits -i fitDiags/fit_diag_B.root -o outs/plots_B --style styles/style_B.yml --toys --xlabel Jet $m_{SD}$ --sigs b150,m150 --project-signals 2,2 --rmap m150:r_q,b150:r_b --bkgs top,vlep,wqq,zqq,zbb,hbb --onto 2017_qcd --cats fail:ptbin*fail;passlow:ptbin*high*;passhigh:ptbin*passlow* --dpi 100 -p 20 --noroot'
fi

# ============================================================================
# STANDARD TEST MATRIX
# Core feature coverage: ~44 images, ~30 seconds
# ============================================================================

if [ "$1" = "A" ] || [ "$1" = "standard" ] || [ "$1" = "all" ]; then
    echo "=== PLOTS_A: Real data with Higgs/Z signals overlaid on QCD, multiple control regions ==="
    echo "Features: data, overlay, unblind"
    echo ""

    run_case "plots_A" \
        'combine_postfits -i fitDiags/fit_diag_A.root -o outs/plots_A --style styles/style_A.yml --data --unblind --sigs hcc,zcc --onto qcd --rmap zcc:z,hcc:r --cats pass:ptbin*pass2016;fail:ptbin*fail*;muCRpass:muonCRpass2016;muCRfail:muonCRfail2016 --bkgs top,other,wqq,wcq,zqq,zbb,hbb --project-signal 50,0 --dpi 100 -p 20 --noroot'
fi

if [ "$1" = "C" ] || [ "$1" = "standard" ] || [ "$1" = "all" ]; then
    echo "=== PLOTS_C: Chi-squared and residual plots with toys data ==="
    echo "Features: chi2, residuals"
    echo ""

    run_case "plots_C" \
        'combine_postfits -i fitDiags/fit_diag_C.root -o outs/plots_C --style styles/style_C.yml --toys --chi2 --residuals --xlabel Jet $m_{reg}$ --dpi 100 -p 20 --noroot'
fi

if [ "$1" = "D" ] || [ "$1" = "standard" ] || [ "$1" = "all" ]; then
    echo "=== PLOTS_D: VH signal search with custom backgrounds and verbose output ==="
    echo "Features: custom signals"
    echo ""

    run_case "plots_D" \
        'combine_postfits -i fitDiags/fit_diag_D.root -o outs/plots_D --style styles/style_D.yml --MC --onto qcd --sigs VH --bkgs qcd,top,Wjets,Zjets,VV,H --rmap VH:rVH --project-signals 3 --xlabel Jet $m_{SD}$ --vv --dpi 100 -p 20 --noroot'
fi

# ============================================================================
# FULL TEST MATRIX
# Comprehensive testing including edge cases: ~244 images, ~2 minutes
# Run before releases or when debugging comprehensive issues
# ============================================================================

if [ "$1" = "full" ] || [ "$1" = "all" ]; then
    echo "=== RUNNING FULL TEST MATRIX ==="
    echo "This includes all *_all variants and multi-year cases"
    echo ""
    echo "Running plots_B_all..."
    run_case "plots_B_all" \
        'combine_postfits -i fitDiags/fit_diag_B.root -o outs/plots_B_all --MC --dpi 100 -p 20 --noroot'

    echo "Running plots_A_all..."
    run_case "plots_A_all" \
        'combine_postfits -i fitDiags/fit_diag_A.root -o outs/plots_A_all --data --unblind --chi2 --residuals --dpi 100 -p 20 --noroot'

    echo "Running plots_Abig..."
    run_case "plots_Abig" \
        'combine_postfits -i fitDiags/fit_diag_Abig.root -o outs/plots_Abig --style styles/style_A.yml --data --unblind --sigs hcc,zcc --onto qcd --rmap zcc:z,hcc:r --cats pass16:ptbin*pass2016;fail16:ptbin*fail2016;pass17:ptbin*pass2017;fail17:ptbin*fail2017;pass18:ptbin*pass2018;fail18:ptbin*fail2018;pass:ptbin*pass*;fail:ptbin*fail*;muCRpass16:muonCRpass2016;muCRfail16:muonCRfail2016;muCRpass17:muonCRpass2017;muCRfail17:muonCRfail2017;muCRpass18:muonCRpass2018;muCRfail18:muonCRfail2018 --bkgs top,other,wqq,wcq,zqq,zbb,hbb --project-signal 50,0 --dpi 100 -p 20 --noroot'

    echo "Running plots_Abig_all..."
    run_case "plots_Abig_all" \
        'combine_postfits -i fitDiags/fit_diag_Abig.root -o outs/plots_Abig_all --data --unblind --dpi 100 -p 20 --noroot'

    echo "Running plots_C_all..."
    run_case "plots_C_all" \
        'combine_postfits -i fitDiags/fit_diag_C.root -o outs/plots_C_all --MC --chi2 --residuals --dpi 100 -p 20 --noroot'

    echo "Running plots_D_all..."
    run_case "plots_D_all" \
        'combine_postfits -i fitDiags/fit_diag_D.root -o outs/plots_D_all --MC --dpi 100 -p 20 --noroot'

fi

echo -e "${GREEN}Done!${NC}"
echo "Output images saved to: outs/"
echo ""
echo "To run visual regression tests:"
echo "  pixi run test-quick      # Quick smoke test"
echo "  pixi run test            # Standard test matrix (default)"
echo "  pixi run test-full       # Full test matrix"
