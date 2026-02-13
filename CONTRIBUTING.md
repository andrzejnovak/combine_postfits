# Contributing to combine_postfits

## Development Setup

```bash
# Clone the repository
git clone https://github.com/andrzejnovak/combine_postfits.git
cd combine_postfits

# Install pixi (if not already installed)
curl -fsSL https://pixi.sh/install.sh | bash

# Install dependencies
pixi install
```

## Running Tests

```bash
# Quick smoke test (~10s)
pixi run test-quick

# Standard tests (~1min) - excludes ROOT-dependent tests
pixi run test

# ROOT-dependent tests only
pixi run test-root

# Full suite including ROOT tests
pixi run test-full
```

## Test Organization

| Directory | Contents |
|---|---|
| `tests/unit/` | Pure function tests (no I/O) |
| `tests/integration/` | API and CLI tests |
| `tests/visual/` | Pixel-perfect visual regression |
| `tests/baseline/` | Reference images for visual tests |
| `tests/fitDiags/` | Input ROOT files |
| `tests/styles/` | Style YAML files |

## Visual Regression Tests

Visual tests enforce **zero tolerance** — any pixel difference fails the test.

### Adding a Visual Test Case

1. Add a `VisualTestCase` to `tests/test_cases.py`
2. Generate baselines: run the CLI command, then copy output to `tests/baseline/`
3. The visual test framework auto-discovers new cases

### Updating Baselines

```bash
# Use the generate-baselines task
pixi run generate-baselines

# Or manually: run the test, then copy output
cp tests/outs/<case>/<fit_type>/<image>.png tests/baseline/<case>/<fit_type>/
```

## Code Style

- Follow existing patterns in the codebase
- Use type hints where practical
- Use `logging` for debug/info output (not `print`)

## Commit Messages

Use [conventional commits](https://www.conventionalcommits.org/):

```
feat: add blind-data support
fix: correct histogram normalization
test: add plot_cov visual regression
ci: update pixi version
docs: update README examples
```

## Pull Requests

1. Create a feature branch
2. Run `pixi run test` before opening a PR
3. Visual test failures will be uploaded as CI artifacts for review
4. New features should include tests
