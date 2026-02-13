# AGENTS.md — combine_postfits

## Project Overview

`combine_postfits` is a Python plotting library for CMS combine `fitDiagnostics` ROOT files. It produces publication-quality postfit/prefit distribution plots with support for signal projection, category merging, and configurable styling.

## Architecture

```
src/combine_postfits/
├── __init__.py
├── make_plots.py        # CLI entry point and orchestration
├── plot_postfits.py     # Core plotting logic (postfit distributions)
├── plot_cov.py          # Covariance matrix plotting
└── utils.py             # Shared helpers (ROOT I/O, histogram handling)
```

- **Entry points**: `combine_postfits` (CLI, via `make_plots:main`) and `combine_postfits_cov`
- **Key dependencies**: `uproot`, `mplhep`, `hist`, `matplotlib`, `scipy`, `numpy`
- **Optional ROOT**: The `--noroot` flag skips ROOT dependency; `uproot` handles most I/O

## Environment & Build

- **Package manager**: [pixi](https://pixi.sh/) (see `pixi.toml`)
- **Build system**: Hatchling (`pyproject.toml`)
- **Python**: ≥3.10, <3.13
- **Install for development**: `pixi install` (sets up conda + editable pip install)

## Testing

Three-tier test strategy driven by pytest markers:

| Command | Scope | Images | Use case |
|---|---|---|---|
| `pixi run test-quick` | Unit + integration + 1 visual | ~6 | Fast feedback |
| `pixi run test` | Unit + integration + standard visuals | ~44 | CI/pre-commit |
| `pixi run test-full` | Everything including edge cases | ~244 | Pre-release |

### Test structure
```
tests/
├── unit/              # Pure function tests (utils, histogram helpers)
├── integration/       # API-level tests (plot generation pipelines)
├── visual/            # Visual regression tests (pixel-perfect comparison)
├── baseline/          # Reference images for visual comparison
├── fitDiags/          # Test input ROOT files (A, B, C, D variants)
├── styles/            # Style YAML files for test cases
├── conftest.py        # Shared fixtures, matplotlib reset
├── test_cases.py      # Test case definitions
└── examples.sh        # Runnable CLI examples / baseline generator
```

### Visual regression
- **Zero tolerance** (`VISUAL_TOLERANCE = 0` in `conftest.py`) — pixel-perfect match required
- Baselines live in `tests/baseline/`
- Failed comparisons output to `tests/failed/` (gitignored)
- Regenerate baselines: `pixi run generate-baselines`

## CI

GitHub Actions workflow at `.github/workflows/ci.yml`:
- **quick**: Runs on every push/PR
- **standard**: Runs on PRs (after quick passes)
- **full**: Runs on schedule (daily) and manual dispatch

## Agent Rules

> **CRITICAL — read before doing anything**

1. **Never push** changes to the remote. Only stage and commit locally.
2. **Never commit** unless the user explicitly asks you to.
3. **Use [Conventional Commits](https://www.conventionalcommits.org/)** for all commit messages (e.g. `feat:`, `fix:`, `refactor:`, `ci:`, `docs:`, `test:`).
4. **Never change `VISUAL_TOLERANCE`** in `tests/conftest.py`. It is set to `0` (pixel-perfect) by design.
5. **Never modify `.root` files** or baseline images directly — regenerate baselines via `pixi run generate-baselines`.

## Code Conventions

- Matplotlib backend set to `Agg` for headless rendering in tests
- Style files are YAML dicts mapping process names → `{label, color, hatch}`
- The root-level `make_plots.py` is a **symlink** to `src/combine_postfits/make_plots.py` for easy user access to the script without installing the package
- `env_combine.yml` is retained for legacy conda environment compatibility

## Common Tasks

### Adding a new test case
1. Add ROOT file to `tests/fitDiags/`
2. Add style YAML to `tests/styles/`
3. Add case definition in `tests/test_cases.py`
4. Add CLI example to `tests/examples.sh`
5. Generate baselines: `pixi run generate-baselines`

### Updating baselines
```bash
pixi run generate-baselines   # Regenerate all
# Then commit updated images in tests/baseline/
```
