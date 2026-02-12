# Test Suite Redesign Plan for combine_postfits

## Overview

Redesign the test suite to support three-tier testing (quick/standard/full) with CLI-to-visual regression tests at zero tolerance, while preserving the self-documenting nature of runnable CLI examples.

## Quick Summary

**Three pixi tasks:**
- `pixi run test-quick` - Fast smoke test (~10s, 6 images)
- `pixi run test` - Standard checks (~30s, 44 images) **[DEFAULT]**
- `pixi run test-full` - Complete matrix (~2min, 244 images)

**Key features:**
- Zero tolerance visual regression testing (CLI → images)
- Runnable CLI examples in `tests/examples.sh`
- Central test definitions in `tests/test_cases.py`
- All A/B/C/D test cases preserved, selectively executed
- Granular control via pytest for power users

**Philosophy**: Keep it simple. This isn't a big library - 3 tasks cover 90% of use cases.

## Current State Analysis

**Test Organization** (62 explicit tests + 244 parametrized visual tests):
- **Unit tests** (41): Well-structured tests for utilities and histogram helpers
- **Integration tests** (20): API-level tests for the `plot()` function
- **Visual baseline tests** (244): Pixel-perfect image comparisons, but **only 6/244 are actually running** (plots_B only)

**Key Issues**:
1. Missing output images for most test cases (A, Abig, C, D)
2. `test.sh` is manual and disconnected from pytest
3. No actual CLI entry point testing
4. Hard-coded paths and brittle test discovery
5. 244 baseline images is excessive for maintenance

## Core Concept: Three-Tier Testing Strategy

1. **Quick** (`test-quick`): Single representative case for fast development (~6 images, <10s)
2. **Standard** (`test`): Core test matrix covering main features (~32 images, ~30s)
3. **Full** (`test-full`): Complete matrix including edge cases (~244 images, ~2min)

Additional pytest invocations available for granular control (unit only, integration only, specific features, etc.)

## Proposed Structure

### Directory Layout

```
combine_postfits/
├── src/combine_postfits/
│   └── ...
├── tests/
│   ├── __init__.py                 # NEW
│   ├── conftest.py                 # KEEP (shared fixtures)
│   ├── test_cases.py               # NEW (central test definitions)
│   ├── generate_examples.py        # NEW (auto-generate examples.sh)
│   ├── examples.sh                 # MODIFIED (auto-generated, replaces test.sh)
│   │
│   ├── unit/                       # KEEP
│   │   ├── __init__.py             # NEW
│   │   ├── test_utils.py           # KEEP
│   │   └── test_hist_helpers.py    # KEEP
│   │
│   ├── integration/                # KEEP
│   │   ├── __init__.py             # NEW
│   │   └── test_plot_api.py        # KEEP
│   │
│   ├── visual/                     # NEW (visual regression tests)
│   │   ├── __init__.py
│   │   └── test_cli_visual.py      # NEW (main visual tests)
│   │
│   ├── baseline/                   # KEEP (baseline images)
│   │   ├── plots_B/                # Quick test (6 images)
│   │   ├── plots_A/                # Standard test (8 images)
│   │   ├── plots_C/                # Standard test (18 images)
│   │   ├── plots_D/                # Standard test (12 images)
│   │   ├── plots_B_all/            # Full matrix only
│   │   ├── plots_A_all/            # Full matrix only
│   │   ├── plots_Abig/             # Full matrix only
│   │   ├── plots_Abig_all/         # Full matrix only
│   │   ├── plots_C_all/            # Full matrix only
│   │   └── plots_D_all/            # Full matrix only
│   │
│   ├── outs/                       # Generated outputs (gitignored)
│   ├── failed/                     # Failed test diffs (gitignored)
│   ├── fitDiags/                   # KEEP (test data)
│   ├── styles/                     # KEEP (style files)
│   └── README.md                   # NEW (test documentation)
│
├── pyproject.toml                  # MODIFIED (pytest config)
└── pixi.toml                       # MODIFIED (test tasks)
```

## Key Components

### 1. Test Case Configuration System (`tests/test_cases.py`)

Central configuration that serves as **both** pytest parameters **and** runnable CLI documentation.

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TestCase:
    """A single test case configuration."""
    name: str
    fitdiag: str                    # Input ROOT file
    style: Optional[str]            # Style YAML (None = auto-style)
    cli_args: List[str]             # CLI arguments
    description: str                # What this tests
    tags: List[str]                 # For filtering: quick, standard, full, feature-*
    expected_images: List[str]      # Expected output image names

    def to_cli_command(self, output_dir: str = "outs") -> str:
        """Generate a complete CLI command for documentation/execution."""
        base = f"combine_postfits -i fitDiags/{self.fitdiag} -o {output_dir}/{self.name}"
        if self.style:
            base += f" --style styles/{self.style}"
        return f"{base} {' '.join(self.cli_args)}"

    def to_bash_script_line(self, dpi: int = 100, processes: int = 20) -> str:
        """Format for bash script with standard options."""
        cmd = self.to_cli_command()
        return f"{cmd} --dpi {dpi} -p {processes} --noroot"
```

**Test cases organized by purpose:**
- **plots_B**: Basic plotting with toys data (QUICK)
- **plots_A**: Real data with signal overlays (STANDARD)
- **plots_C**: Chi-squared and residuals testing (STANDARD)
- **plots_D**: VH analysis example (STANDARD)
- **plots_*_all**: All categories variants (FULL)
- **plots_Abig**: Multi-year analysis (FULL)

Each test case includes:
- Complete CLI arguments
- Feature tags for filtering
- Description of what it tests
- Expected output images

### 2. Visual Regression Tests (`tests/visual/test_cli_visual.py`)

Pytest-based CLI testing that:
- Invokes `combine_postfits` CLI directly via subprocess
- Generates images from CLI commands
- Compares against baselines with 0 tolerance
- Properly integrates with pytest marks

```python
@pytest.mark.parametrize("test_case,fit_type,image_name", generate_test_params(...))
def test_cli_generates_correct_image(test_case, fit_type, image_name, ...):
    """Test that CLI generates pixel-perfect images matching baselines."""
    # Run CLI command
    # Compare with baseline using compare_images(..., tol=0)
    # Save diffs to failed/ for debugging
```

Uses pytest marks for filtering:
- `@pytest.mark.quick` - Quick smoke test
- `@pytest.mark.standard` - Standard test matrix
- `@pytest.mark.full` - Full test matrix
- `@pytest.mark.feature_*` - Feature-specific tests

### 3. Runnable CLI Examples (`tests/examples.sh`)

Auto-generated bash script that replaces `test.sh`, providing:
- Runnable CLI examples for each test case
- Clear documentation of what each case tests
- Grouped by test level (quick/standard/full)
- Color-coded output

**Usage:**
```bash
./tests/examples.sh B          # Run single case
./tests/examples.sh quick      # Run quick cases
./tests/examples.sh standard   # Run standard cases
./tests/examples.sh full       # Run full matrix
./tests/examples.sh all        # Run everything
```

**Generated from test_cases.py:**
```bash
python tests/generate_examples.py  # Regenerate examples.sh
```

### 4. Pytest Configuration (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
minversion = "6.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# Default: run standard (unit + integration + core visual)
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "-m", "not full",  # Exclude full matrix by default
]

markers = [
    "quick: Quick smoke test (single representative case)",
    "standard: Standard test matrix (core features)",
    "full: Full test matrix (all cases, run before release)",
    "visual: Visual regression tests with image comparison",
    "unit: Unit tests for individual functions",
    "integration: Integration tests for API behavior",

    # Feature markers
    "feature_toys: Tests using toys data",
    "feature_data: Tests using real data",
    "feature_chi2: Tests chi-squared calculations",
    "feature_residuals: Tests residual plots",
    "feature_unblind: Tests data unblinding",
    "feature_projection: Tests signal projection",
    "feature_overlay: Tests signal overlay (onto)",
    "feature_multiyear: Tests multi-year analysis",
    "feature_autostyle: Tests auto-styling",
    "feature_custom_signals: Tests custom signal naming",
    "stress: Stress tests (many images, slow)",
]
```

### 5. Simplified Pixi Tasks (`pixi.toml`)

**Philosophy**: Keep tasks minimal - this isn't a large library. Only 3 test tasks needed. Everything else runs via pytest directly.

```toml
[tasks]
# TASK 1: Standard test (DEFAULT)
# Unit + integration + core visual tests (~44 images)
# Use for: CI/CD, pre-commit checks, regular development
test = "pytest tests/ -m 'not full'"

# TASK 2: Quick smoke test
# Unit + integration + single visual case (~6 images)
# Use for: Fast feedback during active development
test-quick = "pytest tests/ -m 'quick or unit or integration'"

# TASK 3: Full test matrix
# Everything including edge cases (~244 images)
# Use for: Pre-release validation, debugging comprehensive issues
test-full = "pytest tests/"

# Utilities (not test execution)
generate-baselines = "./tests/examples.sh all"
update-examples = "python tests/generate_examples.py"
```

**Everything else via pytest directly** (not as pixi tasks):
```bash
# Granular control for developers who need it
pytest tests/unit/                     # Unit tests only
pytest tests/integration/              # Integration tests only
pytest tests/visual/                   # Visual tests only (standard)
pytest tests/visual/ -m full           # Visual tests (full matrix)
pytest tests/ -m feature_chi2          # Feature-specific tests
pytest tests/ -n auto                  # Parallel execution (if pytest-xdist installed)
pytest tests/ --cov=combine_postfits   # With coverage (add pytest-cov if needed)
pytest -k "test_name"                  # Run specific test by name
```

**Rationale**: Three tasks cover 90% of use cases. Power users can use pytest directly for edge cases.

## Test Case Coverage

| Case | Images | Duration | Tags | Description |
|------|--------|----------|------|-------------|
| **plots_B** | 6 | ~3s | quick, standard | Basic toys data with signal projection |
| **plots_A** | 8 | ~5s | standard | Real data with H/Z signals, unblinding |
| **plots_C** | 18 | ~8s | standard | Chi-squared and residual plots |
| **plots_D** | 12 | ~6s | standard | VH analysis with custom signals |
| **plots_B_all** | 30 | ~15s | full | All B categories, auto-styling |
| **plots_A_all** | 28 | ~12s | full | All A categories with chi2 |
| **plots_Abig** | 28 | ~15s | full | Multi-year analysis (2016/17/18) |
| **plots_Abig_all** | 84 | ~40s | full, stress | All Abig categories (stress test) |
| **plots_C_all** | 18 | ~8s | full | All C categories |
| **plots_D_all** | 12 | ~6s | full | All D categories |

**Total**: 244 baseline images across 10 test cases

**Distribution**:
- Quick: 6 images
- Standard: 44 images (6 + 8 + 18 + 12)
- Full: 244 images (all)

## Migration Plan

### Phase 1: Setup (15 minutes)

1. **Create new files**:
   ```bash
   touch tests/__init__.py
   touch tests/unit/__init__.py
   touch tests/integration/__init__.py
   mkdir -p tests/visual
   touch tests/visual/__init__.py
   ```

2. **Create test_cases.py** with all test case definitions

3. **Create generate_examples.py** script

4. **Generate examples.sh**:
   ```bash
   python tests/generate_examples.py
   chmod +x tests/examples.sh
   ```

5. **Update pyproject.toml** with pytest markers and config

6. **Update pixi.toml** with simplified test tasks

### Phase 2: Visual Test Implementation (30 minutes)

1. **Create tests/visual/test_cli_visual.py** with parametrized tests

2. **Test quick mode**:
   ```bash
   # Generate baseline for B if missing
   ./tests/examples.sh B

   # Run quick visual test
   pixi run test-quick
   ```

3. **Verify test discovery**:
   ```bash
   pytest tests/ --collect-only
   ```

### Phase 3: Generate Missing Baselines (optional, 10 minutes)

```bash
# Generate standard baselines
./tests/examples.sh A
./tests/examples.sh C
./tests/examples.sh D

# Verify standard tests pass
pixi run test
```

### Phase 4: Cleanup (5 minutes)

1. **Archive old test.py**:
   ```bash
   mv tests/test.py tests/test_old.py.bak
   ```

2. **Update .gitignore**:
   ```gitignore
   tests/outs/
   tests/failed/
   tests/test_old.py.bak
   ```

3. **Document in README**:
   - Create tests/README.md

### Phase 5: Validation (10 minutes)

```bash
# Run all test levels
pixi run test-quick          # Should pass (~6 images)
pixi run test                # Should pass (~44 images)
pixi run test-full           # Should pass/skip (~244 images)

# Verify test discovery
pytest tests/ --collect-only
```

## Benefits

✅ **Preserves CLI examples**: `examples.sh` is still runnable and readable
✅ **Self-documenting**: Test cases include descriptions and feature tags
✅ **Fast development**: Quick mode runs in ~10s
✅ **Comprehensive testing**: Full matrix available for pre-release checks
✅ **DRY principle**: CLI commands defined once in `test_cases.py`
✅ **Easy to extend**: Add new test case in one place
✅ **CI-friendly**: Different test levels for different triggers
✅ **Backwards compatible**: Existing unit/integration tests unchanged
✅ **Zero tolerance**: Visual tests use `tol=0` as required
✅ **Selective baselines**: Default to standard (~44 images), full available when needed

## Developer Workflow

### The Three Commands You Need

```bash
# 1. During active development - FAST feedback
pixi run test-quick              # ~10s: unit + integration + 1 visual case

# 2. Before commit / CI - BALANCED coverage (DEFAULT)
pixi run test                    # ~30s: unit + integration + core visual tests

# 3. Before release / debugging - COMPREHENSIVE
pixi run test-full               # ~2min: everything including edge cases
```

### CLI Examples (Self-Documentation)

```bash
# View runnable CLI examples
cat tests/examples.sh            # Read examples

# Run specific example manually
./tests/examples.sh B            # Run plots_B example
./tests/examples.sh A            # Run plots_A example

# Regenerate baselines
./tests/examples.sh quick        # Quick baselines only
./tests/examples.sh standard     # Standard baselines (A, B, C, D)
./tests/examples.sh all          # All baselines (full matrix)
```

### Modifying Tests

```bash
# 1. Edit test definitions (single source of truth)
vim tests/test_cases.py

# 2. Regenerate examples.sh (auto-sync)
pixi run update-examples

# 3. Regenerate baselines if CLI output changed
./tests/examples.sh <case>
```

### Power User: Direct Pytest

```bash
# Granular control for specific needs
pytest tests/unit/               # Just unit tests
pytest tests/integration/        # Just integration tests
pytest tests/visual/             # Just visual tests
pytest tests/ -m feature_chi2    # Feature-specific
pytest -k "test_chi2"            # By name pattern
pytest tests/ -n auto            # Parallel (with pytest-xdist)
pytest tests/ --cov              # With coverage (with pytest-cov)
```

## Design Decisions

### Why auto-generate examples.sh?

- **Single source of truth**: Test definitions live in `test_cases.py`
- **DRY principle**: CLI commands defined once, used for both pytest and examples
- **Always in sync**: Can't forget to update examples when test changes
- **Still readable**: Generated bash script is human-readable
- **Still runnable**: Can be executed directly for manual testing

### Why three tiers?

- **Quick**: Fast feedback loop for active development
- **Standard**: Balanced coverage for pre-commit and CI
- **Full**: Comprehensive validation for releases and debugging

### Why pytest marks instead of separate test files?

- **Flexibility**: Can combine marks (e.g., `pytest -m 'full and feature_chi2'`)
- **Single test file**: Visual tests in one place
- **Selective execution**: Easy to run subsets
- **Clear intent**: Marks explicitly show test purpose

### Why keep all 244 baselines?

- **Comprehensive coverage**: Full matrix catches edge cases
- **Selective execution**: Don't need to run all by default
- **Pre-release validation**: Important for ensuring no regressions
- **Cost-effective**: Storage is cheap, debugging production issues is expensive

## Implementation Notes

### Path Handling

Fix brittle path construction in current `test.py`:

```python
# Before (brittle)
path = os.path.dirname(os.path.dirname(combine_postfits.__path__[0]))

# After (robust)
TESTS_DIR = Path(__file__).parent
BASELINE_DIR = TESTS_DIR / "baseline"
OUTS_DIR = TESTS_DIR / "outs"
```

### Test Optimization

Generate all images for a case at once (not per-image) to avoid redundant CLI calls:

```python
@pytest.fixture(scope="module")
def generate_outputs_for_case(request):
    """Generate all outputs for a test case once per module."""
    generated_cases = set()

    def _generate(test_case):
        if test_case.name in generated_cases:
            return

        cmd = test_case.to_bash_script_line()
        subprocess.run(cmd, shell=True, check=True)
        generated_cases.add(test_case.name)

    return _generate
```

### Failed Test Debugging

When visual test fails:
1. Diff saved to `tests/failed/` automatically
2. Includes: expected (baseline), actual (output), and diff image
3. Clear error message with RMS difference
4. Command to update baseline if change is intentional

## Future Enhancements

- **Coverage reporting**: Add `pytest-cov` integration
- **Parallel execution**: Document `pytest-xdist` usage
- **CI/CD templates**: Provide GitHub Actions workflow examples
- **Baseline update tool**: Script to selectively update baselines
- **Performance tracking**: Track test execution time over commits
- **Visual diff viewer**: HTML report for failed visual tests

## Implementation Priorities

### Minimum Viable Product (MVP)

Essential components to get basic functionality working:

1. ✅ **test_cases.py** - Test definitions (core of the system)
2. ✅ **tests/visual/test_cli_visual.py** - Visual regression tests
3. ✅ **pyproject.toml** - Pytest configuration with marks
4. ✅ **pixi.toml** - Three test tasks only
5. ✅ **tests/__init__.py** and subdirectory **__init__.py** files

**Time**: ~30 minutes
**Outcome**: Can run `pixi run test-quick` successfully

### Phase 2: Documentation and Examples

Nice-to-have for better DX:

1. ✅ **generate_examples.py** - Auto-generate examples
2. ✅ **examples.sh** - Runnable CLI examples
3. ✅ **tests/README.md** - Test documentation

**Time**: ~20 minutes
**Outcome**: Self-documenting test examples

### Phase 3: Polish

Optional refinements:

1. Generate missing baselines (A, C, D cases)
2. Update .gitignore
3. Archive old test.py
4. Add CI/CD workflow examples

**Time**: ~20 minutes
**Outcome**: Complete migration

## Quick Start (Post-Implementation)

```bash
# For users after implementation is done:

# Install dependencies
pixi install

# Run tests (pick one)
pixi run test-quick    # Development
pixi run test          # Standard (default)
pixi run test-full     # Comprehensive

# View CLI examples
cat tests/examples.sh

# Run a specific example
./tests/examples.sh B
```

## References

- Current test suite: `tests/test.py`, `tests/test.sh`
- Matplotlib image comparison: `matplotlib.testing.compare.compare_images`
- Pytest parametrization: https://docs.pytest.org/en/stable/parametrize.html
- Pytest markers: https://docs.pytest.org/en/stable/mark.html

---

**Document Status**: ✅ Complete - Ready for implementation
**Last Updated**: 2026-01-05
