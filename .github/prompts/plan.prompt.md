---
description: Create a phased implementation plan for a turboPy feature before writing code
---

# Implementation Planner (turboPy)

Before writing any code, produce a structured plan. Phases should match the turboPy class hierarchy so each phase is independently testable.

## Steps

1. **Clarify the goal** — restate the requirement in one sentence; flag ambiguities.
2. **Research first** — before proposing new code, identify:
   - Existing `Grid` / `GridBase` methods and properties that already do part of the job
   - Existing `ComputeTool` classes (`FiniteDifference`, `FiniteDifference2D`, `PoissonSolver1DRadial`, `BorisPush`, `Interpolators`)
   - Existing `Diagnostic` classes (`PointDiagnostic`, `FieldDiagnostic`, `GridDiagnostic`, `ClockDiagnostic`, `HistoryDiagnostic`)
   - Existing `PhysicsModule` patterns in the repo and in tests/fixtures
   - Whether an existing fixture in `tests/fixtures/{block_on_spring,particle_in_field}/` can be adapted rather than duplicated
3. **Identify dependencies** — external packages (already: `numpy`, `scipy`, `qtoml`, `xarray`), env vars, input-TOML changes, new fixture data.
4. **Break into phases** — each phase ends with a passing test:

   - **Phase 1: Grid / ComputeTool** — any new numerical primitive (sparse operator, interpolator, boundary handler). Landed with unit tests in `tests/test_core.py` or `tests/test_computetools.py`.
   - **Phase 2: PhysicsModule** — the module implementing `update()`, its `_needed_resources`, and any published attributes. Landed with unit tests plus a minimal `Simulation` that runs one step.
   - **Phase 3: Diagnostic** — new diagnostic output type or dispatch case if needed. Landed with unit tests reading the output file.
   - **Phase 4: Integration** — a full-simulation fixture under `tests/fixtures/<name>/` plus a `tests/test_<name>.py` runner, ideally with a 2D variant if the feature touches multi-D grids.

   Not every task needs all four phases — a bug fix might only touch Phase 1.
5. **Identify risks** — anything that could block progress or cause regressions:
   - Grid-dispatch guards that need updating (e.g. `FiniteDifference` raises on 2D)
   - Shared-resource key collisions (`ClassName_attribute` naming)
   - Backward compatibility of TOML input schema
   - Numerical stability at boundaries (r=0, corners of 2D grids)
6. **Define done** — exact acceptance criteria.

## Output Format

```
## Goal
[One-sentence summary]

## Reuse Opportunities
- [Existing class / method / fixture]

## Dependencies
- [Package / TOML field / new fixture file]

## Phases
### Phase 1 — [Name, e.g. "Add cylindrical-2D Poisson operator"]
- [ ] Task A (test file, symbol to add)
- [ ] Task B

### Phase 2 — [Name]
...

## Risks
- [Risk and mitigation]

## Definition of Done
- [ ] All tests pass (`pytest`)
- [ ] Coverage on changed lines ≥ 80% (`pytest --cov=turbopy`)
- [ ] No new pylint errors
- [ ] `CLAUDE.md` updated if the public class hierarchy or Grid dispatch changed
- [ ] `docs/` updated if public API changed
```

## turboPy conventions to apply

- **Registry pattern**: new subclasses of `PhysicsModule` / `ComputeTool` / `Diagnostic` must call `.register("Name", Class)` and be listed in the input TOML by name.
- **Shared resources**: publish via public attributes (auto-shared as `ClassName_attribute`); consume via `_needed_resources`.
- **Grid dispatch**: use `isinstance(grid, GridBase)` for any grid, `isinstance(grid, Grid)` for 1D-only guards. Add explicit `TypeError` / `NotImplementedError` for unsupported grid types.
- **Small, focused modules**: mirror the split in `turbopy/core.py`, `computetools.py`, `diagnostics.py`, `constructors.py`.
