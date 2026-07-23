# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About turboPy

turboPy is a lightweight computational physics framework for rapidly prototyping physics codes. It implements a `Simulation → PhysicsModule → ComputeTool` class hierarchy inspired by the turboWAVE framework. See the [published paper](https://doi.org/10.1016/j.cpc.2020.107607).

## Commands

### Development Setup
```bash
conda env create -f environment.yml
conda activate turbopy
pip install -e .
```

### Testing
```bash
pytest                                          # run all tests
pytest tests/test_core.py                       # run a single test file
pytest tests/test_core.py::TestGrid             # run a single test class
pytest tests/test_core.py::TestGrid::test_r     # run a single test
pytest --cov-report=xml --cov=turbopy tests/    # run with coverage
```

### Documentation
```bash
cd docs && make html      # build HTML docs
cd docs && make latexpdf  # build PDF docs
```

### Linting
Use pylint with `variable-rgx=[a-z0-9_]{1,30}$` in `.pylintrc` to allow single-character variable names (common in physics code).

## Architecture

### Core Class Hierarchy (`turbopy/core.py`)

All user-extensible classes use the **DynamicFactory (registry) pattern**: subclasses register themselves by name and are instantiated by the `Simulation` based on input configuration.

```
DynamicFactory  ←  base registry class with .register() / .lookup()
├── PhysicsModule   ←  physical dynamics, must implement update()
├── ComputeTool     ←  numerical methods, shared between modules
└── Diagnostic      ←  data collection and output
```

**`Simulation`** is the root owner. It reads input dicts (from TOML via `constructors.py`), instantiates all components, and runs the main loop:
```
prepare_simulation()  →  while clock.is_running(): fundamental_cycle()  →  finalize_simulation()
```

Each `fundamental_cycle()` step:
1. Run all `Diagnostic.diagnose()`
2. Call `PhysicsModule.reset()` on all modules
3. Call `PhysicsModule.update()` on all modules
4. Advance `SimulationClock`

### Resource Sharing

Modules exchange data through `Simulation.all_shared_resources`:
- **Publishing:** A module's public attributes are automatically shared under the key `ClassName_attribute`.
- **Consuming:** Modules declare what they need in `_needed_resources` dict; the simulation wires them up after `exchange_resources()` is called on all modules.

### Grid (`turbopy/core.py`)

Grids share a common abstract base and are selected via the `"coordinate_system"` key on the input `Grid` dict. `Simulation.read_grid_from_input()` dispatches to the right class.

```
GridBase (ABC)  ←  requires generate_field() and create_interpolator()
├── Grid                 ←  1D Cartesian / cylindrical / spherical (default)
├── Grid2DCartesian      ←  "coordinate_system": "cartesian2d"
└── Grid2DCylindrical    ←  "coordinate_system": "cylindrical2d"
```

- **`Grid` (1D):** input `N` (or `dr`/`dx`), `min`/`max` (or `x_min`/`x_max`/`r_min`/`r_max`). Properties: `r`, `cell_edges`, `cell_centers`, `cell_widths`, `cell_volumes`, `interface_areas`, `r_inv`.
- **`Grid2DCartesian`:** input `Nx`/`dx`, `Ny`/`dy`, `x_min`/`x_max`, `y_min`/`y_max`. Properties: `x`, `y`, `x_centers`, `y_centers`, `x_widths`, `y_widths`, `XX`, `YY` (meshgrid with `indexing='ij'`), `cell_volumes` (`dx*dy`), `shape == (Nx, Ny)`.
- **`Grid2DCylindrical`:** input `Nr`/`dr`, `Nz`/`dz`, `r_min`/`r_max`, `z_min`/`z_max`. Distinct from 1D `"cylindrical"` (which is radial-only). Properties: `r`, `z`, `RR`, `ZZ`, `r_inv`, `r_inv_2d`, `cell_volumes` (annular, `pi*(r_{i+1}^2 - r_i^2)*dz_j`).

Use `isinstance(grid, GridBase)` for any grid, `isinstance(grid, Grid)` to detect 1D specifically.

`generate_field(num_components=1, placement_of_points=...)` returns a zero array with placement options `"edge-centered"`, `"cell-centered"`, and staggered variants (`"x-edge-y-cell"` etc.). `create_interpolator((x0, y0))` returns a bilinear interpolator for edge-centered 2D fields.

### Provided Implementations

- **`turbopy/computetools.py`**: `PoissonSolver1DRadial`, `PoissonSolver2D` (Dirichlet `φ=0` on all boundaries; supports both 2D grid types via `FiniteDifference2D` + `scipy.sparse.linalg.spsolve`), `FiniteDifference` (1D-only; raises `TypeError` on a 2D grid), `FiniteDifference2D` (Kronecker-product sparse operators for 2D grids: `ddx`/`ddy`/`del2_x`/`del2_y` for Cartesian, `ddr`/`ddz`/`del2_r`/`del2_z` for cylindrical, `laplacian()` dispatches on grid type — Cartesian returns `del2_x + del2_y`, cylindrical returns `del2_r + del2_z` with the `(1/r) d/dr` term; expects fields flattened in C order), `BorisPush`, `Interpolators`.
- **`turbopy/diagnostics.py`**: `PointDiagnostic`, `FieldDiagnostic`, `GridDiagnostic` (writes both axes for 2D grids), `ClockDiagnostic`, `HistoryDiagnostic` (supports 1D and both 2D grid types; 2D grids attach `x`/`y` or `r`/`z` coordinates to the xarray dataset); output utilities for CSV and NPY formats.
- **`turbopy/constructors.py`**: `construct_simulation_from_toml(filename)` helper.

### Adding a Custom Module

```python
from turbopy import PhysicsModule

class MyModule(PhysicsModule):
    def update(self):
        ...  # required

PhysicsModule.register("MyModule", MyModule)
```

Same pattern applies for `ComputeTool` and `Diagnostic`.

### Test Fixtures

Integration tests in `tests/test_bos.py` and `tests/test_pif.py` use full simulation fixtures in `tests/fixtures/block_on_spring/` and `tests/fixtures/particle_in_field/`. Each also has a `*_2d_cartesian.py` variant exercising the 2D grid path. Unit test fixtures are in `tests/conftest.py`.
