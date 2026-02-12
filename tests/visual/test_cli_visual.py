"""
Visual regression tests for CLI output.

Tests verify pixel-perfect image matching against baselines (zero tolerance).

Usage:
    pixi run test-quick    # Unit + integration + 1 visual
    pixi run test          # Unit + integration + handpicked visuals
    pixi run test-full     # Unit + integration + all visuals
"""

import pytest
import subprocess
import sys
from pathlib import Path
import shutil
from matplotlib.testing.compare import compare_images

from tests.test_cases import TEST_CASES
from tests.conftest import VISUAL_TOLERANCE

TESTS_DIR = Path(__file__).parent.parent
BASELINE_DIR = TESTS_DIR / "baseline"
OUTS_DIR = TESTS_DIR / "outs"
FAILED_DIR = TESTS_DIR / "failed"


# Marker assignment based on tier
# quick tests also run in standard (but not full-only tests)
TIER_MARKERS = {
    "quick": [pytest.mark.quick, pytest.mark.standard],
    "standard": [pytest.mark.standard],
    "full": [pytest.mark.full],
}


def discover_images(case_name: str, fit_type: str) -> list:
    """Find baseline images for a test case."""
    baseline_path = BASELINE_DIR / case_name / fit_type
    if not baseline_path.exists():
        return []
    return sorted([p.name for p in baseline_path.glob("*.png")])


def generate_test_params():
    """Generate pytest parameters from test cases and baseline images."""
    params = []
    for case in TEST_CASES.values():
        for fit_type in ["prefit", "fit_s"]:
            for img in discover_images(case.name, fit_type):
                marks = [pytest.mark.visual] + TIER_MARKERS[case.tier]
                params.append(pytest.param(
                    case, fit_type, img,
                    marks=marks,
                    id=f"{case.name}-{fit_type}-{img.replace('.png', '')}"
                ))
    return params


# Session-scoped cache for CLI runs
@pytest.fixture(scope="session")
def cli_runner():
    """Run CLI commands, caching results to avoid redundant runs."""
    cache = {}

    def run(test_case):
        if test_case.name in cache:
            return cache[test_case.name]

        cmd = [
            str(Path(sys.executable).parent / "combine_postfits"),
            "-i", f"fitDiags/{test_case.fitdiag}",
            "-o", f"outs/{test_case.name}",
        ]
        if test_case.style:
            cmd.extend(["--style", f"styles/{test_case.style}"])
        cmd.extend(test_case.cli_args)
        cmd.extend(["--dpi", "100", "-p", "10", "--noroot"])

        result = subprocess.run(
            cmd,
            cwd=TESTS_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300,
        )
        cache[test_case.name] = result
        return result

    return run


@pytest.mark.parametrize("test_case,fit_type,image_name", generate_test_params())
def test_visual_regression(test_case, fit_type, image_name, cli_runner):
    """
    Verify CLI produces pixel-perfect images matching baselines.
    
    Zero tolerance: any pixel difference fails the test.
    """
    baseline = BASELINE_DIR / test_case.name / fit_type / image_name
    output = OUTS_DIR / test_case.name / fit_type / image_name

    if not baseline.exists():
        pytest.skip(f"Baseline not found: {baseline}")

    # Always regenerate to catch code regressions
    result = cli_runner(test_case)
    if result.returncode != 0:
        pytest.fail(
            f"CLI failed:\n"
            f"Command: {test_case.to_cli_command()}\n"
            f"Stderr: {result.stderr}"
        )

    if not output.exists():
        pytest.fail(f"Output not generated: {output}")

    # Compare with zero tolerance
    diff = compare_images(str(baseline), str(output), tol=VISUAL_TOLERANCE, in_decorator=True)

    if diff is not None:
        # Save baseline/result/diff triplet for easy inspection
        stem = image_name.replace(".png", "")
        fail_dir = FAILED_DIR / f"{test_case.name}-{fit_type}-{stem}"
        if fail_dir.exists():
            shutil.rmtree(fail_dir)
        fail_dir.mkdir(parents=True)
        shutil.copy(diff['expected'], fail_dir / "baseline.png")
        shutil.copy(diff['actual'], fail_dir / "result.png")
        shutil.copy(diff['diff'], fail_dir / "diff.png")

        pytest.fail(
            f"Image mismatch (RMS: {diff['rms']:.6f})\n"
            f"  Baseline: {baseline}\n"
            f"  Result:   {output}\n"
            f"  Diff:     {fail_dir / 'diff.png'}\n"
            f"  All outputs: {fail_dir}/\n"
            f"To update: cp '{output}' '{baseline}'"
        )
