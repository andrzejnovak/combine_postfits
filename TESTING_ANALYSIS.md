# Testing Infrastructure Analysis & TDD Improvement Proposal

**Package**: `combine_postfits` - Plotting library for CMS combine fitDiagnostics  
**Date**: January 2026

---

## 1. Current State Analysis

### 1.1 Infrastructure Overview

| Component | Current State | Assessment |
|-----------|---------------|------------|
| **Test Runner** | pytest with manual shell scripts | ⚠️ Fragmented |
| **Visual Testing** | matplotlib's `compare_images` (tol=0) | ✅ Strict, correct |
| **Baseline Storage** | Git-tracked PNGs (~25MB) | ⚠️ Heavy but acceptable |
| **CI** | GitHub Actions, 5 parallel jobs | ✅ Good parallelization |
| **Coverage** | Only integration (CLI → output) | ❌ No unit tests |
| **Test Data** | fitDiagnostics ROOT files (~27MB) | ✅ Realistic |

### 1.2 Test Architecture

```
tests/
├── baseline/              # ~200 PNG reference images (25MB)
│   ├── plots_A/
│   │   ├── prefit/
│   │   └── fit_s/
│   └── ... (A, Abig, B, C, D variants)
├── fitDiags/              # fitDiagnostics ROOT files (27MB)
├── styles/                # YAML style configs
├── test.sh                # Shell orchestration (generates outputs)
├── test.py                # pytest image comparisons
└── outs/                  # Generated outputs (not tracked)
```

### 1.3 Current Test Flow

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│  test.sh A  │ ──► │ combine_     │ ──► │ outs/plots_A/ │
│ (CLI calls) │     │ postfits CLI │     │ (new images)  │
└─────────────┘     └──────────────┘     └───────────────┘
                                               │
                                               ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ baseline/    │◄───│ compare_     │◄───│  test.py     │
│ plots_A/     │    │ images(tol=0)│    │  (pytest)    │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 1.4 Visual Testing Philosophy (CRITICAL)

**Zero tolerance is correct for this library.** 

This is a high-stakes physics plotting library where:
- Every visual change must be intentional and reviewed
- Pixel-perfect reproducibility is a feature, not a bug
- False negatives (missed changes) are worse than false positives (flagged changes)
- Baseline updates require explicit human approval

The goal is NOT to reduce test failures, but to **catch every visual change** for review.

---

## 2. Identified Weaknesses

### 2.1 Critical Issues

| Issue | Impact | TDD Blocker? |
|-------|--------|--------------|
| **No unit tests** | Can't test individual functions | ✅ Yes |
| **Slow feedback loop** | Full plot generation required | ✅ Yes |
| **Shell script dependency** | test.sh must run before test.py | ⚠️ Moderate |
| **No fixture isolation** | Tests depend on execution order | ⚠️ Moderate |
| **Missing test categories** | No edge case, error path, or regression tests | ✅ Yes |

### 2.2 TDD Anti-Patterns

1. **Two-Step Testing**: `test.sh` must run before `test.py` - not self-contained
2. **All-or-Nothing Testing**: Can't test `plot_postfits.plot()` without full CLI
3. **No Mocking**: Hard to test styling logic without actual ROOT files
4. **No Fast Feedback**: Every test requires image generation

### 2.3 Missing Test Coverage

```python
# Currently untested:
- utils.py (format_legend, format_categories, merge_hists, etc.)
- plot_postfits.py internal functions (hist_dict_fcn, chi2_calc)
- Error handling paths
- Edge cases (empty histograms, missing channels, negative values)
- Style parsing and validation
- Argument parsing edge cases
```

---

## 3. Proposed Testing Architecture

### 3.1 Multi-Layer Testing Pyramid

```
                    ┌─────────────────────┐
                    │   Visual Tests       │  ← KEEP: tol=0, human review
                    │   (pixel-perfect)    │     Slow, high-value
                    └──────────┬──────────┘
                               │
               ┌───────────────┴───────────────┐
               │       Integration Tests        │  ← NEW: API-level
               │   (plot() returns, no images)  │     Fast, catches regressions
               └───────────────┬───────────────┘
                               │
       ┌───────────────────────┴───────────────────────┐
       │                  Unit Tests                    │  ← NEW: Instant
       │   (utils, parsing, data transforms)            │     TDD-friendly
       └───────────────────────────────────────────────┘
```

### 3.2 Recommended Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_utils.py        # Pure function tests
│   ├── test_parsing.py      # Argument parsing
│   └── test_style.py        # Style dict processing
├── integration/
│   ├── test_plot_api.py     # plot() function behavior (no image compare)
│   └── test_hist_loading.py # Histogram extraction from fitDiags
├── visual/
│   ├── conftest.py          # Visual test config
│   ├── test_images.py       # Image comparison (tol=0, strict)
│   └── generate_outputs.py  # Replaces test.sh
├── baseline/                # Reference images (existing)
├── fitDiags/                # fitDiagnostics ROOT files (existing)
├── styles/                  # Test style configs (existing)
└── outs/                    # Generated outputs (not tracked)
```

---

## 4. Visual Testing Strategy

### 4.1 Keep Zero Tolerance

The current `tol=0` is correct. Visual tests should:
- Fail on ANY pixel difference
- Generate diff images for human review
- Require explicit baseline updates

### 4.2 Improve Failure Reporting

Current test.py already copies failed images to `tests/failed/`. Enhance with:

```python
# tests/visual/conftest.py
import pytest
import os
import shutil
from pathlib import Path

@pytest.fixture(autouse=True)
def setup_failed_dir():
    """Ensure clean failed directory for each run"""
    failed_dir = Path(__file__).parent.parent / "failed"
    if failed_dir.exists():
        shutil.rmtree(failed_dir)
    failed_dir.mkdir(exist_ok=True)
    yield failed_dir

def pytest_html_results_table_row(report, cells):
    """Add image diffs to HTML report if available"""
    if hasattr(report, 'diff_image'):
        cells.insert(2, f'<td><img src="{report.diff_image}" width="200"/></td>')
```

### 4.3 Baseline Update Workflow

```bash
# NEVER auto-update baselines. Always:
# 1. Review diff images in tests/failed/
# 2. Confirm changes are intentional
# 3. Manually copy approved outputs to baseline/

# Helper script for intentional updates:
# tests/update_baseline.sh
#!/bin/bash
echo "⚠️  BASELINE UPDATE - Review changes carefully!"
echo "Copying: tests/outs/$1 → tests/baseline/$1"
read -p "Confirm? (y/N) " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cp -r "tests/outs/$1/"* "tests/baseline/$1/"
    echo "Done. Commit with descriptive message."
fi
```

### 4.4 Consolidate test.sh into pytest

Replace shell script orchestration with pytest fixtures:

```python
# tests/visual/generate_outputs.py
"""
Generate test outputs - replaces test.sh
Run with: pytest tests/visual/generate_outputs.py --generate
"""
import subprocess
import pytest
from pathlib import Path

TESTS_DIR = Path(__file__).parent.parent
FITDIAGS = TESTS_DIR / "fitDiags"
OUTS = TESTS_DIR / "outs"
STYLES = TESTS_DIR / "styles"

DPI = 100
OPTS = "--noroot"

TEST_CONFIGS = {
    "A": {
        "all": f"combine_postfits --dpi {DPI} -i {FITDIAGS}/fit_diag_A.root -o {OUTS}/plots_A_all --data --unblind --chi2 --residuals {OPTS}",
        "styled": f"combine_postfits --dpi {DPI} -i {FITDIAGS}/fit_diag_A.root -o {OUTS}/plots_A --style {STYLES}/style_A.yml --data --unblind --sigs hcc,zcc --onto qcd --rmap zcc:z,hcc:r --cats 'pass:ptbin*pass2016;fail:ptbin*fail*;muCRpass:muonCRpass2016;muCRfail:muonCRfail2016' --bkgs top,other,wqq,wcq,zqq,zbb,hbb --project-signal 50,0 {OPTS}",
    },
    # ... other test cases
}

@pytest.fixture(scope="session")
def generate_outputs(request):
    """Generate all test outputs before visual comparison"""
    test_set = request.config.getoption("--test-set", default="A")
    for name, cmd in TEST_CONFIGS.get(test_set, {}).items():
        subprocess.run(cmd, shell=True, check=True)
```

---

## 5. Unit Test Examples

### 5.1 Utils Testing (Fast, TDD-friendly)

```python
# tests/unit/test_utils.py
import pytest
import numpy as np
import hist
from combine_postfits.utils import (
    format_categories, 
    merge_hists, 
    fill_colors, 
    extract_mergemap,
    adjust_lightness,
    tgasym_to_hist,
)


class TestFormatCategories:
    def test_single_category(self):
        assert format_categories(["cat1"], n=2) == "cat1"
    
    def test_two_categories_same_line(self):
        assert format_categories(["cat1", "cat2"], n=2) == "cat1,cat2"
    
    def test_three_categories_wraps(self):
        result = format_categories(["cat1", "cat2", "cat3"], n=2)
        assert "cat1,cat2" in result
        assert "\n" in result
        assert "cat3" in result
    
    def test_custom_line_length(self):
        cats = ["a", "b", "c", "d", "e"]
        result = format_categories(cats, n=3)
        lines = result.split("\n")
        assert len(lines) == 2  # 3 on first line, 2 on second


class TestMergeHists:
    @pytest.fixture
    def sample_hists(self):
        h1 = hist.new.Reg(10, 0, 100).Weight()
        h1.view().value[:] = np.array([10, 20, 30, 40, 50, 40, 30, 20, 10, 5])
        h2 = hist.new.Reg(10, 0, 100).Weight()
        h2.view().value[:] = np.array([5, 10, 15, 20, 25, 20, 15, 10, 5, 2])
        return {"qcd": h1, "wjets": h2, "signal": h1 * 0.1}
    
    def test_merge_sums_histograms(self, sample_hists):
        merge_map = {"ewk": ["qcd", "wjets"]}
        result = merge_hists(sample_hists.copy(), merge_map)
        assert "ewk" in result
        np.testing.assert_array_almost_equal(
            result["ewk"].values(),
            sample_hists["qcd"].values() + sample_hists["wjets"].values()
        )
    
    def test_merge_preserves_originals(self, sample_hists):
        merge_map = {"ewk": ["qcd", "wjets"]}
        result = merge_hists(sample_hists.copy(), merge_map)
        assert "qcd" in result
        assert "wjets" in result
    
    def test_merge_missing_hist_warns(self, sample_hists, caplog):
        merge_map = {"combined": ["qcd", "nonexistent"]}
        merge_hists(sample_hists.copy(), merge_map)
        assert "not available" in caplog.text
    
    def test_merge_all_missing_warns(self, sample_hists, caplog):
        merge_map = {"combined": ["foo", "bar"]}
        merge_hists(sample_hists.copy(), merge_map)
        assert "No histograms available" in caplog.text


class TestFillColors:
    def test_fills_missing_colors(self):
        style = {
            "sig": {"label": "Signal", "color": None, "hatch": None}
        }
        result = fill_colors(style, cmap=["#ff0000", "#00ff00"])
        assert result["sig"]["color"] == "#ff0000"
    
    def test_preserves_existing_colors(self):
        style = {
            "sig": {"label": "Signal", "color": "#0000ff", "hatch": None}
        }
        result = fill_colors(style, cmap=["#ff0000"])
        assert result["sig"]["color"] == "#0000ff"
    
    def test_cycles_colors_when_exhausted(self):
        style = {
            "a": {"label": "A", "color": None, "hatch": None},
            "b": {"label": "B", "color": None, "hatch": None},
            "c": {"label": "C", "color": None, "hatch": None},
        }
        result = fill_colors(style, cmap=["#ff0000", "#00ff00"])
        # Should cycle or lighten
        assert result["a"]["color"] is not None
        assert result["b"]["color"] is not None
        assert result["c"]["color"] is not None


class TestExtractMergemap:
    def test_extracts_contains_entries(self):
        style = {
            "ewk": {"label": "EWK", "contains": ["wjets", "zjets"]},
            "qcd": {"label": "QCD", "contains": None},
        }
        result = extract_mergemap(style)
        assert result == {"ewk": ["wjets", "zjets"]}
    
    def test_empty_style_returns_empty(self):
        assert extract_mergemap({}) == {}


class TestAdjustLightness:
    def test_lightens_color(self):
        lighter = adjust_lightness("#808080", amount=1.5)
        # Should be lighter (higher RGB values)
        assert lighter != "#808080"
    
    def test_darkens_color(self):
        darker = adjust_lightness("#808080", amount=0.5)
        assert darker != "#808080"
```

### 5.2 Style Parsing Tests

```python
# tests/unit/test_style.py
import pytest
from combine_postfits.utils import clean_yaml, prep_yaml


class TestCleanYaml:
    def test_standardizes_none_string(self):
        style = {"sig": {"label": "Sig", "color": "None", "hatch": "NONE"}}
        result = clean_yaml(style)
        assert result["sig"]["color"] is None
        assert result["sig"]["hatch"] is None
    
    def test_handles_raw_strings(self):
        style = {"sig": {"label": 'r"$H_{bb}$"', "color": "red", "hatch": None}}
        result = clean_yaml(style)
        assert result["sig"]["label"] == "$H_{bb}$"
    
    def test_parses_contains_string_to_list(self):
        style = {"ewk": {"label": "EWK", "color": "blue", "hatch": None, "contains": "wjets zjets"}}
        result = clean_yaml(style)
        assert result["ewk"]["contains"] == ["wjets", "zjets"]
    
    def test_warns_unexpected_keys(self, caplog):
        style = {"sig": {"label": "Sig", "color": "red", "unknown_key": "value"}}
        clean_yaml(style)
        assert "Unexpected key" in caplog.text
```

### 5.3 Integration Tests (API-level, no image comparison)

```python
# tests/integration/test_plot_api.py
import pytest
import uproot
import matplotlib.pyplot as plt
from pathlib import Path
from combine_postfits import plot_postfits

FITDIAGS = Path(__file__).parent.parent / "fitDiags"


@pytest.fixture
def fitdiag_A():
    return uproot.open(FITDIAGS / "fit_diag_A.root")


@pytest.fixture
def sample_style():
    return {
        "data": {"label": "Data", "color": "black", "hatch": None},
        "total_signal": {"label": "Signal", "color": "red", "hatch": None},
        "qcd": {"label": "QCD", "color": "yellow", "hatch": "///"},
        "hcc": {"label": r"$H_{cc}$", "color": "blue", "hatch": None},
        "zcc": {"label": r"$Z_{cc}$", "color": "green", "hatch": None},
    }


@pytest.fixture(autouse=True)
def cleanup_plots():
    yield
    plt.close('all')


class TestPlotReturns:
    def test_returns_figure_and_axes(self, fitdiag_A, sample_style):
        fig, (ax, rax) = plot_postfits.plot(
            fitdiag_A, 
            fit_type="prefit",
            style=sample_style,
        )
        assert fig is not None
        assert ax is not None
        assert rax is not None
        assert isinstance(fig, plt.Figure)
    
    def test_returns_none_for_empty_channels(self, fitdiag_A, sample_style):
        result = plot_postfits.plot(
            fitdiag_A,
            fit_type="prefit", 
            cats=[],
            style=sample_style,
        )
        assert result == (None, (None, None))


class TestPlotOptions:
    def test_blind_mode(self, fitdiag_A, sample_style):
        fig, (ax, rax) = plot_postfits.plot(
            fitdiag_A,
            fit_type="prefit",
            blind=True,
            style=sample_style,
        )
        # Data should not be plotted - check legend
        labels = [t.get_text() for t in ax.get_legend().get_texts()]
        assert "Data" not in labels
    
    @pytest.mark.parametrize("fit_type", ["prefit", "fit_s"])
    def test_fit_types(self, fitdiag_A, sample_style, fit_type):
        fig, _ = plot_postfits.plot(
            fitdiag_A,
            fit_type=fit_type,
            style=sample_style,
        )
        assert fig is not None
    
    def test_category_selection(self, fitdiag_A, sample_style):
        fig, (ax, rax) = plot_postfits.plot(
            fitdiag_A,
            fit_type="prefit",
            cats=["ptbin0pass2016"],
            style=sample_style,
        )
        assert fig is not None
    
    def test_onto_stacking(self, fitdiag_A, sample_style):
        fig, _ = plot_postfits.plot(
            fitdiag_A,
            fit_type="prefit",
            onto="qcd",
            style=sample_style,
        )
        # Should not raise, QCD plotted as step
        assert fig is not None


class TestPlotContent:
    def test_axis_labels_set(self, fitdiag_A, sample_style):
        fig, (ax, rax) = plot_postfits.plot(
            fitdiag_A,
            fit_type="prefit",
            style=sample_style,
        )
        assert rax.get_xlabel() != ""
        assert ax.get_ylabel() != ""
    
    def test_legend_present(self, fitdiag_A, sample_style):
        fig, (ax, rax) = plot_postfits.plot(
            fitdiag_A,
            fit_type="prefit",
            style=sample_style,
        )
        assert ax.get_legend() is not None
    
    def test_chi2_annotation(self, fitdiag_A, sample_style):
        fig, (ax, rax) = plot_postfits.plot(
            fitdiag_A,
            fit_type="prefit",
            chi2=True,
            style=sample_style,
        )
        # Check for chi2 text in ratio axis
        texts = [t.get_text() for t in rax.texts]
        assert any("chi" in t.lower() or "χ" in t for t in texts) or len(rax.artists) > 0
```

---

## 6. Implementation Roadmap

### Phase 1: Unit Tests (Week 1)
- [ ] Create `tests/conftest.py` with shared fixtures
- [ ] Implement `tests/unit/test_utils.py`
- [ ] Implement `tests/unit/test_style.py`
- [ ] Verify tests run in < 1 second

### Phase 2: Integration Tests (Week 2)
- [ ] Create `tests/integration/test_plot_api.py`
- [ ] Add parameterized tests for all plot options
- [ ] Test error handling paths
- [ ] Test edge cases (negative histograms, missing channels)

### Phase 3: Consolidate Visual Tests (Week 3)
- [ ] Move visual test logic into `tests/visual/`
- [ ] Create `generate_outputs.py` to replace `test.sh`
- [ ] Keep `tol=0` - add better diff image reporting
- [ ] Document baseline update procedure

### Phase 4: CI Enhancement (Week 4)
- [ ] Add unit/integration tests to CI (fast jobs)
- [ ] Keep visual tests as separate slow job
- [ ] Improve artifact upload for failed visual tests
- [ ] Add HTML report with diff images

---

## 7. Configuration

### 7.1 pyproject.toml additions

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "visual: marks visual regression tests (require output generation)",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]

[project.optional-dependencies]
test = [
    "pytest>=7.0",
    "pytest-xdist",
    "pytest-cov",
    "pillow",  # for image comparison
]
```

### 7.2 tests/conftest.py

```python
# tests/conftest.py
import pytest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import uproot

TESTS_DIR = Path(__file__).parent
FITDIAGS = TESTS_DIR / "fitDiags"


@pytest.fixture(scope="session")
def fitdiag_A():
    """fitDiagnostics file for test case A"""
    return uproot.open(FITDIAGS / "fit_diag_A.root")


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
    matplotlib.rcParams.update(matplotlib.rcParamsDefault)


@pytest.fixture
def base_style():
    """Minimal valid style dict"""
    return {
        "data": {"label": "Data", "color": "black", "hatch": None},
        "total_signal": {"label": "Signal", "color": "red", "hatch": None},
        "total_background": {"label": "Background", "color": "gray", "hatch": None},
        "total": {"label": "Total", "color": "black", "hatch": None},
    }
```

---

## 8. Agentic TDD Workflow

### Quick Feedback Loops

```bash
# Instant unit test feedback (< 1s)
pytest tests/unit/ -x -q

# Integration tests (~5s)
pytest tests/integration/ -x

# Full visual test suite (slow, ~2min)
cd tests && bash test.sh A && pytest test.py -x

# Run only specific visual test case
cd tests && bash test.sh A && pytest test.py -k "plots_A"
```

### Development Cycle

```
┌─────────────────────────────────────────────────────────────┐
│  1. Write failing unit test  ──────────────────► < 1 sec   │
│  2. Implement minimal code   ──────────────────► iterate   │
│  3. Write integration test   ──────────────────► < 5 sec   │
│  4. Visual test only when rendering changes ──► manual     │
│  5. Review diffs, update baseline if approved ► explicit   │
└─────────────────────────────────────────────────────────────┘
```

### Visual Test Update Procedure

```bash
# 1. Run tests, observe failures
cd tests && bash test.sh A && pytest test.py

# 2. Review diff images
ls tests/failed/  # Contains: diff.png, *-baseline.png, *-test.png

# 3. If changes are intentional, update baseline
# MANUAL: Copy approved images from outs/ to baseline/
cp tests/outs/plots_A/prefit/pass_prefit.png tests/baseline/plots_A/prefit/

# 4. Commit with descriptive message
git add tests/baseline/
git commit -m "Update baseline: [describe visual change]"
```

---

## 9. Summary

| Priority | Change | Effort | Impact |
|----------|--------|--------|--------|
| 🔴 High | Add unit tests for utils.py | Medium | Enables TDD, fast feedback |
| 🔴 High | Add integration tests for plot() | Medium | Catches API regressions |
| 🟡 Medium | Consolidate test.sh into pytest | Medium | Self-contained tests |
| 🟡 Medium | Better diff image reporting | Low | Easier review of failures |
| 🟢 Low | Separate CI jobs for unit vs visual | Low | Faster CI feedback |

### Key Principles

1. **Keep tol=0** - Every pixel matters in physics plots
2. **Unit tests for speed** - TDD requires instant feedback
3. **Integration tests for coverage** - Test API without images
4. **Visual tests for approval** - Human review of all changes
5. **Explicit baseline updates** - Never auto-accept changes

---

## 10. Discussion Points

1. **Test organization**: Should we keep test.py or fully migrate to pytest structure?

2. **CI structure**: Keep 5 parallel visual jobs, or consolidate with unit tests in fast job?

3. **Baseline storage**: Current git-tracked approach works, or consider Git LFS for large files?

4. **Minimal test data**: Worth creating a smaller (~5MB) fitDiagnostics for faster unit/integration tests?

---

*Document for discussion. Implementation requires review and prioritization.*
