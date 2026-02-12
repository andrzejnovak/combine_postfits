# Test Suite for combine_postfits

This directory contains a three-tier test suite with zero-tolerance visual regression testing.

## Quick Start

```bash
# Install dependencies
pixi install

# Run tests (pick one)
pixi run test-quick    # Fast smoke test (~10s, 6 images)
pixi run test          # Standard test matrix (~30s, 44 images) [DEFAULT]
pixi run test-full     # Full matrix (~2min, 244 images)
```

## Test Organization

```
tests/
├── unit/              # Unit tests for individual functions
├── integration/       # API-level integration tests
├── visual/            # CLI-to-image visual regression tests
├── baseline/          # Reference images for visual tests (git-tracked)
├── outs/              # Generated test outputs (gitignored)
├── failed/            # Failed test diffs (gitignored)
├── fitDiags/          # Test input files (ROOT files)
├── styles/            # Test style configurations (YAML)
├── test_cases.py      # Central test case definitions
└── examples.sh        # Runnable CLI examples (auto-generated)
```

## Test Levels

### Quick (Development)
- **Command**: `pixi run test-quick`
- **Duration**: ~10 seconds
- **Coverage**: Unit + Integration + Single visual case (plots_B)
- **Images**: 6 baseline images
- **Use**: Fast feedback during active development

### Standard (Default)
- **Command**: `pixi run test`
- **Duration**: ~30 seconds
- **Coverage**: Unit + Integration + Core visual tests (B, A, C, D)
- **Images**: ~44 baseline images
- **Use**: Pre-commit checks, CI/CD pipelines

### Full (Pre-release)
- **Command**: `pixi run test-full`
- **Duration**: ~2 minutes
- **Coverage**: Everything including edge cases and stress tests
- **Images**: ~244 baseline images
- **Use**: Before releases, debugging comprehensive issues

## Running Tests

### Basic Usage

```bash
# Development workflow
pixi run test-quick          # Fast smoke test

# Before commit
pixi run test                # Standard test matrix

# Before release
pixi run test-full           # Full comprehensive tests
```

### Granular Control (Direct Pytest)

```bash
# Specific test types
pytest tests/unit/                     # Unit tests only
pytest tests/integration/              # Integration tests only
pytest tests/visual/                   # Visual tests (standard)
pytest tests/visual/ -m full           # Visual tests (full matrix)

# Feature-specific
pytest tests/ -m feature_chi2          # Chi2 tests
pytest tests/ -m feature_toys          # Toys data tests
pytest tests/ -m feature_data          # Real data tests

# By name pattern
pytest -k "test_chi2"                  # Tests matching pattern

# With coverage
pytest tests/ --cov=combine_postfits   # Requires pytest-cov

# Parallel execution
pytest tests/ -n auto                  # Requires pytest-xdist
```

## Test Case Definitions

All test cases are centrally defined in `test_cases.py`. Each case includes:

- CLI command arguments
- Expected output images
- Feature tags for filtering
- Description of what it tests

**Test Cases**:

| Case | Images | Duration | Description |
|------|--------|----------|-------------|
| **plots_B** | 6 | ~3s | Basic toys data with signal projection (QUICK) |
| **plots_A** | 8 | ~5s | Real data with H/Z signals, unblinding (STANDARD) |
| **plots_C** | 18 | ~8s | Chi-squared and residual plots (STANDARD) |
| **plots_D** | 12 | ~6s | VH analysis with custom signals (STANDARD) |
| **plots_B_all** | 30 | ~15s | All B categories, auto-styling (FULL) |
| **plots_A_all** | 28 | ~12s | All A categories with chi2 (FULL) |
| **plots_Abig** | 28 | ~15s | Multi-year analysis 2016/17/18 (FULL) |
| **plots_Abig_all** | 84 | ~40s | All Abig categories - stress test (FULL) |
| **plots_C_all** | 18 | ~8s | All C categories (FULL) |
| **plots_D_all** | 12 | ~6s | All D categories (FULL) |

## Visual Regression Testing

Visual tests verify **pixel-perfect** (zero tolerance) image matching:

### How It Works

1. CLI command runs: `combine_postfits -i ... -o ...`
2. Output images generated in `outs/`
3. Compared against baseline images in `baseline/`
4. Any pixel difference = test fails
5. Diff saved to `failed/` for debugging

### When Tests Fail

If a visual test fails:

1. **Check the diff**: Look in `tests/failed/` for comparison images
2. **Investigate**: Is the change intentional or a bug?
3. **If intentional**: Update the baseline (see below)
4. **If bug**: Fix the code

### Updating Baselines

```bash
# Option 1: Generate via examples.sh
cd tests
./examples.sh B              # Specific case
./examples.sh quick          # Quick baselines
./examples.sh standard       # Standard baselines (A,B,C,D)
./examples.sh all            # All baselines (full matrix)

# Option 2: Copy from test output
cp tests/outs/plots_B/prefit/fail_prefit.png tests/baseline/plots_B/prefit/

# Option 3: Regenerate all (use with caution!)
./examples.sh all
rm -rf baseline/*
cp -r outs/* baseline/
```

## CLI Examples (Self-Documentation)

The `examples.sh` file contains runnable CLI commands for each test case.

### Usage

```bash
# View examples
cat tests/examples.sh

# Run specific example
./tests/examples.sh B        # Run plots_B example
./tests/examples.sh A        # Run plots_A example

# Run multiple examples
./tests/examples.sh quick    # Quick cases only
./tests/examples.sh standard # Standard cases
./tests/examples.sh all      # Everything
```

### Auto-Generated

**Important**: `examples.sh` is auto-generated from `test_cases.py`.

To modify examples:
1. Edit `test_cases.py`
2. Run: `pixi run update-examples`
3. The script will regenerate `examples.sh`

This ensures test definitions and CLI examples stay in sync.

## Modifying Tests

### Adding a New Test Case

1. **Edit `test_cases.py`**:
   ```python
   TEST_CASES["plots_E"] = TestCase(
       name="plots_E",
       fitdiag="fit_diag_E.root",
       style="style_E.yml",
       cli_args=["--MC", "--chi2"],
       description="New test case for feature X",
       tags=["standard", "full", "feature_X"],
   )
   ```

2. **Regenerate examples.sh**:
   ```bash
   pixi run update-examples
   ```

3. **Generate baselines**:
   ```bash
   ./tests/examples.sh E
   mkdir -p baseline/plots_E
   cp -r outs/plots_E/* baseline/plots_E/
   ```

4. **Run tests**:
   ```bash
   pixi run test
   ```

### Modifying Existing Test

1. Edit the test case in `test_cases.py`
2. Run `pixi run update-examples`
3. Regenerate baselines for that case
4. Verify tests pass

## Troubleshooting

### Issue: Visual tests fail with size mismatches

**Cause**: DPI mismatch between baseline and generated images

**Solution**:
```bash
# Regenerate baselines with correct DPI (100)
./tests/examples.sh <case>
cp outs/<case>/*/* baseline/<case>/
```

### Issue: Missing baseline images

**Cause**: Baseline not generated yet

**Solution**:
```bash
./tests/examples.sh <case>
mkdir -p baseline/<case>
cp -r outs/<case>/* baseline/<case>/
```

### Issue: Tests are slow

**Cause**: Running full matrix by default

**Solution**: Use selective testing
```bash
pixi run test-quick          # Quick mode
pytest -m 'not full'         # Exclude full matrix
pytest tests/unit/           # Unit tests only
```

### Issue: CLI command not found

**Cause**: combine_postfits not installed or wrong environment

**Solution**:
```bash
# Ensure package is installed
pixi install

# Check installation
which combine_postfits
combine_postfits --help
```

## CI/CD Integration

Recommended workflow:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Pixi
        uses: prefix-dev/setup-pixi@v0.4.1

      - name: Quick tests (on every push)
        run: pixi run test-quick

      - name: Standard tests (on PR)
        if: github.event_name == 'pull_request'
        run: pixi run test

      - name: Full tests (on release)
        if: github.event_name == 'release'
        run: pixi run test-full
```

## Development Workflow

```bash
# 1. During active development
pixi run test-quick              # Fast feedback (~10s)

# 2. Before committing
pixi run test                    # Standard checks (~30s)

# 3. Before creating PR
pixi run test                    # Verify no regressions

# 4. Before release
pixi run test-full               # Comprehensive validation (~2min)
```

## Test Statistics

- **Total test cases**: 10 (B, A, C, D + variants)
- **Total baseline images**: 244
- **Unit tests**: 41
- **Integration tests**: 20
- **Visual regression tests**: 244 (parametrized from baselines)

## Design Principles

1. **Zero tolerance**: Visual tests use pixel-perfect comparison (`tol=0`)
2. **DRY**: Test definitions in one place (`test_cases.py`)
3. **Self-documenting**: Examples auto-generated from test definitions
4. **Selective execution**: Run only what you need (quick/standard/full)
5. **Fail fast**: Tests fail immediately on any regression

## Further Reading

- **Test redesign plan**: See `TESTING_REDESIGN_PLAN.md`
- **Pytest markers**: See `pyproject.toml` for all available markers
- **Pytest docs**: https://docs.pytest.org/
