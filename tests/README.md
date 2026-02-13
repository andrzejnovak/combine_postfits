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

### ROOT (Full Validation)
- **Command**: `pixi run test-root`
- **Duration**: ~2 minutes
- **Coverage**: Everything including ROOT-dependent tests (plot_cov, rmap)
- **Use**: Full validation including features requiring native ROOT

## Running Tests

### Basic Usage

```bash
# Development workflow
pixi run test-quick          # Fast smoke test

# Before commit
pixi run test                # Standard test matrix

# Full validation (including ROOT-dependent tests)
pixi run test-root           # All tests including ROOT
```

### Granular Control (Direct Pytest)

```bash
# Specific test types
pytest tests/unit/                     # Unit tests only
pytest tests/integration/              # Integration tests only
pytest tests/visual/                   # Visual tests (standard)
pytest tests/ -m root                  # ROOT-dependent tests only

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

`examples.sh` provides runnable examples corresponding to the test cases.
It is hand-maintained but should be kept in sync with `test_cases.py`.

## Modifying Tests

### Adding a New Test Case

1. **Edit `test_cases.py`**:
   ```python
   TEST_CASES["plots_E"] = VisualTestCase(
       name="plots_E",
       fitdiag="fit_diag_E.root",
       style="style_E.yml",
       tier="standard",
       cli_args=["--MC", "--chi2"],
       description="New test case for feature X",
   )
   ```

2. **Add to examples.sh**:
   Copy an existing block in `tests/examples.sh` and update it for the new case.

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
2. **Update examples.sh**:
   Update the corresponding entry in `tests/examples.sh`.
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
pytest -m 'not root'         # Exclude ROOT tests
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
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Pixi
        uses: prefix-dev/setup-pixi@v0.9.4

      - name: Quick tests (on every push)
        run: pixi run test-quick

      - name: Standard tests (on PR)
        if: github.event_name == 'pull_request'
        run: pixi run test

      - name: ROOT tests (on schedule/dispatch)
        if: github.event_name == 'schedule'
        run: pixi run test-root
```

## Development Workflow

```bash
# 1. During active development
pixi run test-quick              # Fast feedback (~10s)

# 2. Before committing
pixi run test                    # Standard checks (~30s)

# 3. Before creating PR
pixi run test                    # Verify no regressions

# 4. Full validation (including ROOT features)
pixi run test-root               # All tests including ROOT-dependent
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

- **Pytest markers**: See `pyproject.toml` for all available markers
- **Pytest docs**: https://docs.pytest.org/
