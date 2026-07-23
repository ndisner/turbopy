---
description: Systematically diagnose and fix pytest failures, import errors, or environment issues in turboPy
---

# Build / Test Error Resolution

Work through the error systematically. Fix root causes — do not suppress warnings or skip checks.

## Process

### 1. Capture the full error
Include the complete traceback (not just the last line). Note:
- Full traceback (all frames)
- File and line number
- The pytest node id or command that failed
- Whether it reproduces with `pytest -x <node_id>` in isolation

### 2. Categorize the error

| Category | Signals |
|----------|---------|
| **Import / module** | `ModuleNotFoundError`, `ImportError: cannot import name X`, circular import warnings |
| **Environment** | `command not found: pytest`, wrong Python version, missing `numpy`/`scipy`/`qtoml`/`xarray` |
| **Install / packaging** | `pyproject.toml` parse errors, `pip install -e .` failing, version-attr resolution errors |
| **Type / attribute** | `AttributeError`, `TypeError: unexpected keyword`, missing method on subclass |
| **Numerical** | `AssertionError` on `np.allclose`, `RuntimeWarning: invalid value`, NaN/Inf in output |
| **Shape / dispatch** | `ValueError: shapes ... not aligned`, `TypeError` from a grid-dispatch guard (e.g. `FiniteDifference` on a 2D grid) |
| **Fixture** | `fixture 'X' not found`, `FileNotFoundError` from a fixture path, TOML parse errors in `tests/fixtures/**/*.toml` |
| **Lint** | pylint messages; recall `.pylintrc` allows single-letter names (`variable-rgx=[a-z0-9_]{1,30}$`) |

### 3. Fix strategy

- **Import errors** — verify the symbol is exported from `turbopy/__init__.py`; check for circular imports between `core.py`, `computetools.py`, `diagnostics.py`; verify `pip install -e .` completed.
- **Environment** — confirm `conda activate turbopy` was run. Re-check `environment.yml` if a dependency is missing.
- **Packaging** — for `pyproject.toml` issues, verify `[tool.setuptools.dynamic] version = {attr = "turbopy.__version__.__version__"}` resolves; the module must be importable before build.
- **Type / attribute** — read the class hierarchy. Registry pattern: check the class is registered (`PhysicsModule.register(...)`); check `_needed_resources` names match published resource keys (`ClassName_attribute`).
- **Numerical failures** — do NOT loosen `rtol`/`atol` without understanding why. Investigate whether the physics or discretization changed. Compare against an analytic reference on a smaller grid to isolate.
- **Shape / dispatch** — check grid type: `isinstance(grid, GridBase)` for any grid, `isinstance(grid, Grid)` for 1D specifically. `FiniteDifference` is 1D-only; use `FiniteDifference2D` for 2D grids. `HistoryDiagnostic` is 1D-only.
- **Fixture errors** — check the fixture's `.toml` file exists and parses; verify any `output_directory` paths exist or are tmp-path fixtures.
- **Lint** — fix the code; pylint disables should be rare and commented with a reason.

### 4. Verify the fix

Re-run the failing test in isolation:
```bash
pytest -x <node_id>
```

Then run the full suite to confirm no regressions:
```bash
pytest
```

For coverage-sensitive changes:
```bash
pytest --cov-report=term-missing --cov=turbopy tests/
```

### 5. Check for related issues
A single root cause often produces multiple failures. After fixing, grep for the same pattern elsewhere in `turbopy/` and `tests/`.

## Rules

- Never use `pytest -k` or `pytest.mark.skip` to hide a failure without a written justification.
- Never suppress a `RuntimeWarning` with `warnings.filterwarnings` without understanding the numerical origin.
- Never widen a numerical tolerance (`rtol`, `atol`) as a shortcut for fixing a bug.
- Never modify a lockfile / env spec (`environment.yml`, `pyproject.toml`) as the *first* diagnostic step — reproduce the error first.
- Never delete `tests/fixtures/**/reference*.csv` (or similar recorded reference data) to make a test pass. Regenerating reference data requires explicit confirmation.
