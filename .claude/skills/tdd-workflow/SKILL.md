---
name: tdd-workflow
description: Use this skill when writing new features, fixing bugs, or refactoring in the turboPy Python physics framework. Enforces test-driven development with pytest and ≥80% coverage.
---

# Test-Driven Development Workflow (turboPy / pytest)

This skill drives all code work in this repo through a strict RED → GREEN → REFACTOR loop using `pytest`.

## When to activate

- Adding a new `PhysicsModule`, `ComputeTool`, `Diagnostic`, or `Grid` variant
- Fixing a numerical or dispatch bug in `turbopy/core.py`, `turbopy/computetools.py`, or `turbopy/diagnostics.py`
- Refactoring existing code that already has test coverage
- Adding a new integration fixture (e.g. a new physics scenario)

## Core principles

1. **Tests before code.** No implementation until a failing test exists.
2. **Coverage floor of 80%** measured with `pytest --cov=turbopy`.
3. **Physics correctness**, not just execution — assert against analytic solutions where possible.

## Test taxonomy for turboPy

### Unit tests
Live in `tests/test_core.py`, `tests/test_computetools.py`, `tests/test_diagnostics.py`. Exercise a single method or property in isolation:

- Grid properties (`cell_volumes`, `interface_areas`, `r_inv`, meshgrid shapes)
- `generate_field()` return shape for each `placement_of_points` value
- Finite-difference operator matrices (compare to a hand-computed small case)
- `Interpolators` bilinear values on known inputs

### Integration tests
Live in `tests/test_<scenario>.py` and consume a fixture under `tests/fixtures/<scenario>/`. Exercise a full `Simulation`:

- `test_bos.py` + `tests/fixtures/block_on_spring/` — mechanics loop
- `test_pif.py` + `tests/fixtures/particle_in_field/` — particle/field coupling
- Each has a `*_2d_cartesian.py` variant exercising the 2D grid path

Use these as templates when adding a new scenario. Do **not** copy them wholesale without regenerating reference data.

## Workflow

### Step 0 — Detect the runner
The runner is always `pytest`. Setup follows `CLAUDE.md`:

```bash
conda env create -f environment.yml
conda activate turbopy
pip install -e .
```

### Step 1 — Restate the behavior under test
Write one sentence describing the observable behavior. Example:
> "`Grid2DCartesian.cell_volumes` returns `dx * dy` for every cell, with shape `(Nx, Ny)`."

### Step 2 — Write the failing test

```python
# tests/test_core.py
class TestGrid2DCartesian:
    def test_cell_volumes_equals_dx_times_dy(self):
        grid = Grid2DCartesian({
            "Nx": 4, "Ny": 3,
            "x_min": 0.0, "x_max": 1.0,
            "y_min": 0.0, "y_max": 3.0,
        })
        assert grid.cell_volumes.shape == (4, 3)
        assert np.allclose(grid.cell_volumes, 0.25 * 1.0)
```

Use Arrange-Act-Assert. Prefer `np.allclose` / `np.testing.assert_allclose` over `==` for float arrays.

### Step 3 — Run and confirm RED

```bash
pytest tests/test_core.py::TestGrid2DCartesian::test_cell_volumes_equals_dx_times_dy -x
```

If the test passes on the first run without any implementation, the test is not strong enough — revise it.

### Step 4 — Minimum implementation
Write only enough code in `turbopy/` to make the test pass. No abstractions, no configuration knobs that no test drives.

### Step 5 — Run and confirm GREEN

```bash
pytest tests/test_core.py::TestGrid2DCartesian::test_cell_volumes_equals_dx_times_dy -x
```

Then run the full suite to catch regressions:

```bash
pytest
```

### Step 6 — Refactor
Improve names, remove duplication, split large functions. Keep the suite green after every change. `pytest -x --lf` reruns just the last failures.

### Step 7 — Coverage check

```bash
pytest --cov-report=term-missing --cov=turbopy tests/
```

Target ≥80% on new/changed lines. If a branch is intentionally uncovered (e.g. a `raise NotImplementedError` that guards an unsupported case), leave a one-line comment saying why.

## turboPy testing patterns

### Testing a new PhysicsModule
1. Register the module (`PhysicsModule.register("MyModule", MyModule)`) inside the test module or a fixture.
2. Build a minimal input dict with a `Grid`, a `Clock`, your module, and (if needed) a `Diagnostic`.
3. Run `simulation.run()` and assert on published resources or diagnostic output files.

### Testing published/consumed resources
```python
def test_module_publishes_field(minimal_sim_with_my_module):
    minimal_sim_with_my_module.prepare_simulation()
    resources = minimal_sim_with_my_module.all_shared_resources
    assert "MyModule_field" in resources
    assert resources["MyModule_field"].shape == (10,)
```

### Testing grid dispatch
```python
def test_finite_difference_rejects_2d_grid():
    grid_2d = Grid2DCartesian({...})
    with pytest.raises(TypeError):
        FiniteDifference({}, owner=..., grid=grid_2d)
```

### Testing against an analytic solution
Prefer coarse grids where the analytic answer is a small closed form. Compare with `np.testing.assert_allclose(actual, expected, rtol=..., atol=...)` and pick tolerances that reflect the discretization order, not machine epsilon.

## Common mistakes

### Wrong: asserting only shape
```python
result = solver.solve(rhs)
assert result.shape == (N,)   # says nothing about correctness
```

### Right: assert shape *and* values
```python
result = solver.solve(rhs)
assert result.shape == (N,)
np.testing.assert_allclose(result, analytic_solution, rtol=1e-6)
```

### Wrong: skipping RED
Writing test + implementation together and only running the test at the end. You lose the guarantee that the test can actually fail.

### Wrong: overusing mocks
`numpy`, `scipy`, and turboPy's own classes are cheap to instantiate. Use them directly. Mocks are for I/O boundaries (file writes, subprocess calls), not core numerics.

### Wrong: shared mutable state between tests
Do not rely on a previous test's registrations or published resources. Each test gets its own `Simulation`.

## Coverage & CI

```bash
pytest --cov-report=xml --cov=turbopy tests/
```

Produces `coverage.xml` for CI upload. Locally, use `--cov-report=term-missing` to see uncovered lines inline.

## Success criteria

- All tests green
- New/changed code ≥ 80% covered
- No skipped or xfailed tests without a comment explaining why
- Numerical assertions include tolerances appropriate to the discretization
