# turboPy — Development Notes

Rolling notes for contributors. Covers changes since the last tagged release, work in progress on active branches, and known follow-ups. Not a user-facing changelog.

## Changes Since `v2020.10.14`

### Features

- **2D grids** (PR #189, merged) — new `GridBase` ABC, `Grid2DCartesian`, and `Grid2DCylindrical` classes. New `FiniteDifference2D` compute tool with Kronecker-product sparse operators. 2D fixtures added under `tests/fixtures/{block_on_spring,particle_in_field}_2d_cartesian.py`.
- **Wall-clock timing** (PR #169, merged) — `Simulation` records `wall_start_time`, `wall_end_time`, `wall_time` around `run()`; printed at completion.
- **Gridless simulations** (PR #164) — `Simulation` can run without a grid for pure-particle or lumped-quantity setups.
- **NPY diagnostic helper** (PR #159) — `NPYOutputUtility` complements the existing CSV utility for `FieldDiagnostic`.
- **File-writing during simulation** (PR #156) — diagnostics can now stream output during the main loop rather than only at finalize.

### Packaging & Maintenance

- **`pyproject.toml`** (PR #190, merged) — migrated from `setup.py` to PEP 621. Requires Python ≥3.11. Version resolved dynamically from `turbopy/__version__.py`.
- **`.history/` untracked** — removed the VS Code Local History directory from version control.
- Version bumps, NumPy `int64` fixes (PRs #182, #185, #186), Sphinx doc build fixes (PR #187), Travis CI badge/URL updates (PR #188).
- Complexity reductions in `read_diagnostics_from_input` (PRs #175, #176).

### Documentation

- README updates: attribution section (PR #166), published-paper reference (PR #162), formatting fixes.
- Sphinx contributing guide (PR #187).

## In Progress on `2D-Solve`

This branch adds the numerical infrastructure needed for 2D field solves that build on the merged 2D grid work.

- **`FiniteDifference2D`** — added `del2_r()` (cylindrical Laplacian radial part, `d²/dr² + (1/r) d/dr`, uses `Grid2DCylindrical.r_inv_2d` so the operator remains finite at `r=0`). Generalized `laplacian()` to dispatch on grid type: Cartesian returns `del2_x + del2_y`; cylindrical returns `del2_r + del2_z`.
- **`PoissonSolver2D`** — new `ComputeTool`. Solves `∇²φ = source` with Dirichlet `φ=0` on all four boundaries. Supports both `Grid2DCartesian` and `Grid2DCylindrical`. Boundary rows of the sparse Laplacian are replaced with identity rows and the corresponding source entries zeroed at solve time; interior solve is via `scipy.sparse.linalg.spsolve`.
- **`HistoryDiagnostic`** — 2D grid support. Removed the `NotImplementedError` guards for `Grid2DCartesian` and `Grid2DCylindrical`. `initialize()` now attaches `x`/`y` (cartesian) or `r`/`z` (cylindrical) coordinates to the xarray dataset.
- **Test coverage** — full FD2D operator coverage (18 tests) using polynomial reference solutions (centered-difference is exact on quadratics); 6 PoissonSolver2D tests; 2 HistoryDiagnostic 2D-grid round-trip tests (netCDF write + coord verification). Suite total: 128 tests, all green.

## Ongoing Tasks (Deferred)

- **`PoissonSolver2D` boundary conditions** — v1 is Dirichlet `φ=0` only. Extend to (a) configurable Dirichlet values per edge, then (b) Neumann and mixed BCs. Will need an input schema.
- **`PoissonSolver2D` scale-out** — direct `spsolve` is fine for the fixture-sized grids we test. For production-sized runs (say ≳ 10⁵ unknowns) consider `cg`/`bicgstab` with an ILU preconditioner, or `pyamg`. Benchmark before switching.
- **`FiniteDifference2D` boundary rows** — first- and second-derivative operators leave boundary rows as degenerate stencils (missing neighbors treated as zero). This is fine when a downstream solver overrides them (as `PoissonSolver2D` now does for Dirichlet BC), but callers using these operators for open-boundary problems get garbage on the boundary. Options: one-sided/upwind boundary rows, or a shared BC-application helper.
- **`FiniteDifference2D` cell-centered variants** — current operators assume edge-centered fields. Add cell-centered variants if diagnostics or physics modules need them.
- **`HistoryDiagnostic` on 2D vector/tensor fields** — only scalar 2D fields are tested. Multi-component field storage on 2D grids should be verified end-to-end.
- **Documentation** — `docs/` Sphinx pages don't yet cover `Grid2DCartesian`, `Grid2DCylindrical`, `FiniteDifference2D`, or `PoissonSolver2D`. Add API pages and one worked example.
- **Deprecation cleanup** — `publish_resource()` still emits a `DeprecationWarning` (see `turbopy/core.py:513`). Audit downstream users and remove the shim on the next major release.

## Open Development Questions

- **`laplacian()` API on 1D grids** — currently `FiniteDifference2D.laplacian()` requires a 2D grid; 1D users go through `FiniteDifference`. Should there be a unified `laplacian()` entry point that dispatches across 1D and 2D grids for a cleaner API, or is the split intentional?
- **Coordinate units in `HistoryDiagnostic`** — 2D coords default to `units='m'` and `long_name` of `x`/`y`/`r`/`z`. Should these be user-overridable via the trace input (e.g., for normalized or scaled coordinates)?
- **Zero-boundary flag on Poisson** — `PoissonSolver2D` currently *always* forces boundary rows to identity + zero RHS. When we add configurable BCs, keep this as the default or require the user to opt in?
- **Return type from `PoissonSolver2D.solve`** — currently returns a NumPy `ndarray` shaped like the grid. Should it also expose a flat-vector interface for callers that already work in flattened space (matching `FiniteDifference2D`'s C-order convention)?
- **2D fixtures for the new solver** — do we want a `poisson_2d` integration fixture under `tests/fixtures/` analogous to `block_on_spring/`, or are the current unit-level tests in `test_computetools.py` sufficient until a real physics use-case lands?
- **Sphinx doc generation for 2D APIs** — is a single 2D subpage sufficient, or should each new class get its own page?
