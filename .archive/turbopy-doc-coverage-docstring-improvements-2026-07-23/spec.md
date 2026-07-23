# Spec: turboPy Documentation Coverage & Docstring Improvements

## OPEN QUESTIONS

1. **Scope of user-guide narrative pages.** Should new pages such as `simulation_lifecycle.rst`, `grids.rst`, `physics_modules.rst`, etc. include worked examples (code snippets that a user can run), or be limited to prose that references the autodoc API pages? Recommendation: include short, non-runnable illustrative snippets modeled on the style of the existing `sharing_data.rst`. Confirm before coder proceeds.
2. **Split of `api.rst`.** Should the current single `api.rst` (which uses `automodule ... :members:` for each of `turbopy.core`, `turbopy.computetools`, `turbopy.diagnostics`) be broken into per-class pages using `autoclass`, or left as one dump and supplemented with narrative pages? Recommendation: keep `api.rst` as the exhaustive reference and add narrative pages that link into it via `:class:` roles. Confirm.
3. **Deprecated methods.** `PhysicsModule.publish_resource`, `PhysicsModule.inspect_resource`, and `Diagnostic.inspect_resource` are marked "Deprecated" via bolded text. Should these use `.. deprecated::` Sphinx directive instead so they render distinctly? Recommend yes.
4. **`autosummary`.** Not currently enabled. Adding it would produce nicer index tables. Recommend enabling it as a small conf.py addition; confirm.
5. **`Grid.set_grid_points`, `set_volume_and_area_elements`, and all the `set_*_volumes` / `set_*_areas` / `set_interface_volumes` helpers.** These are technically public (no leading underscore) but are internal setup. Recommendation: leave as-is (or convert to leading-underscore in a separate PR) and do NOT gate the acceptance criteria on them.
6. **`OutputUtility`, `PrintOutputUtility`, `CSVOutputUtility`, `NPYOutputUtility`, `IntervalHandler` — user-facing?** They are not registered under any `DynamicFactory` registry but are imported/used by the built-in diagnostics. Confirm whether to document as public API or as "internal helpers". Recommendation: document as public since users writing custom diagnostics may compose with them.

---

## 1. Style, Conventions, Reference

- **Docstring style:** numpydoc (NumPy style). Confirmed by `docs/conf.py` (`napoleon_numpy_docstring = True`, `napoleon_google_docstring = False`) and by existing well-documented symbols such as `turbopy.core.Simulation`, `turbopy.core.Grid`, `turbopy.core.SimulationClock`, `turbopy.core.Grid2DCartesian`, `turbopy.core.Grid2DCylindrical`.
- **Reference exemplars to copy from:**
  - `Simulation` (`turbopy/core.py` lines 25–150) for class-level docstrings with a deeply nested `Parameters` `dict` argument and an `Attributes` section.
  - `Grid2DCartesian` (`turbopy/core.py` lines 1057–1114) for numpydoc block that lists shapes/dtypes in Attributes.
  - `SimulationClock` (`turbopy/core.py` lines 646–692) for a simpler Parameters/Attributes template.
  - `FiniteDifference2D` (`turbopy/computetools.py` lines 489–521) for a compute tool with `Raises` and prose explaining the numeric convention.
  - `HistoryDiagnostic` (`turbopy/diagnostics.py` lines 543–614) for `Examples` and `References` sections in numpydoc.
- **RST style for narrative pages:** copy structure of `docs/sharing_data.rst` — H1 with `====`, H2 with `----`, code samples via `::` fenced RST literal blocks, `:class:` cross-references to autodoc.

---

## 2. Audit of Sphinx Documentation (`docs/`)

### Existing pages

- `/Users/ndisner/github/turbopy/docs/index.rst` — landing page; toctree only references `getting_started`, `sharing_data`, `api`.
- `/Users/ndisner/github/turbopy/docs/getting_started.rst` — conda setup, pytest, one-line pointer to an example app. Very thin.
- `/Users/ndisner/github/turbopy/docs/sharing_data.rst` — the only narrative concept page; covers `_resources_to_share` / `_needed_resources`.
- `/Users/ndisner/github/turbopy/docs/api.rst` — single autodoc dump of `turbopy.core`, `turbopy.diagnostics`, `turbopy.computetools`. Missing `turbopy.constructors`. Also contains a typo: `PhyiscsModule` (should be `PhysicsModule`).
- `/Users/ndisner/github/turbopy/docs/conf.py` — Sphinx config.
- `/Users/ndisner/github/turbopy/docs/Makefile` and `docs/make.bat` — standard.
- `/Users/ndisner/github/turbopy/docs/_static/custom.css` — theme override (empty/unused).

### Pages to CREATE

Each is a new file under `docs/` and must be added to the toctree in `index.rst`.

1. `docs/overview.rst` — Framework mental model. Explain `Simulation → PhysicsModule → ComputeTool` hierarchy, `Diagnostic` on the side, the `DynamicFactory` registry pattern, and the `fundamental_cycle` loop (reference `Simulation.fundamental_cycle` in `turbopy/core.py`). One conceptual diagram in ASCII/text (no image assets required).
2. `docs/simulation_lifecycle.rst` — Deep dive on `Simulation.run()`, `prepare_simulation()`, and `finalize_simulation()`; the ordering of `read_grid_from_input → read_clock_from_input → read_tools_from_input → read_modules_from_input → read_diagnostics_from_input → initialize()` calls; and where `exchange_resources`/`inspect_resources` fire. Source: `turbopy/core.py` lines 173–261.
3. `docs/clock.rst` — Configuring `SimulationClock` via the `"Clock"` input dict (start_time, end_time, num_steps vs dt, print_time). Note the `RuntimeError` raised when `end_time - start_time` is not an integer multiple of `dt`. Source: `turbopy/core.py` lines 646–737.
4. `docs/grids.rst` — Full documentation of the grid system: `GridBase` abstract API (`generate_field`, `create_interpolator`, `coordinate_system` class attribute), the 1D `Grid` and its three coordinate systems (`cartesian`, `cylindrical`, `spherical` — the difference is in `set_volume_and_area_elements`), `Grid2DCartesian`, `Grid2DCylindrical`. Explain field placement options (`edge-centered`, `cell-centered`, `x-edge-y-cell`, `x-cell-y-edge`, `r-edge-z-cell`, `r-cell-z-edge`). Explain the `isinstance(grid, GridBase)` vs `isinstance(grid, Grid)` idiom. Source: `turbopy/core.py` lines 740–1460.
5. `docs/physics_modules.rst` — How to subclass `PhysicsModule`, required `update()`, optional `reset()`, `initialize()`, `exchange_resources()`. Registration idiom `PhysicsModule.register(...)`. Cross-link to `sharing_data.rst`. Source: `turbopy/core.py` lines 426–591.
6. `docs/compute_tools.rst` — How to subclass `ComputeTool`, when to use one instead of a `PhysicsModule` (numerical methods shared across modules), `find_tool_by_name`, `custom_name`. Covers the stock tools: `PoissonSolver1DRadial`, `FiniteDifference` (1D only, raises `TypeError` on 2D grid), `FiniteDifference2D` (matrix layout: C-order flatten, Kronecker-product construction), `BorisPush`, `Interpolators`. Source: `turbopy/core.py` lines 594–644 and all of `turbopy/computetools.py`.
7. `docs/diagnostics.rst` — Diagnostic base class, `diagnose()`, `initialize()`, `finalize()`, `_needed_resources`. The default filename/directory conventions from `Simulation.read_diagnostics_from_input`. Cover the built-in diagnostics: `PointDiagnostic`, `FieldDiagnostic` (with `dump_interval` / `write_interval` distinction), `GridDiagnostic` (writes both axes for 2D), `ClockDiagnostic`, `HistoryDiagnostic` (**1D grids only** — raises `NotImplementedError` on 2D grids). Also document the `OutputUtility` helper classes and `IntervalHandler`. Source: `turbopy/core.py` lines 1463–1566 and all of `turbopy/diagnostics.py`.
8. `docs/dynamic_factory.rst` — The registry pattern. `DynamicFactory.register(name, cls, override=False)`, `.lookup(name)`, `.is_valid_name(name)`. Explain the `_factory_type_name` / `_registry` protocol subclasses must implement. Show the full pattern for adding a custom `PhysicsModule`, `ComputeTool`, or `Diagnostic`. Source: `turbopy/core.py` lines 377–423.
9. `docs/input_files.rst` — TOML input format via `construct_simulation_from_toml`. Enumerate the accepted top-level keys (`Grid`, `Clock`, `PhysicsModules`, `Diagnostics`, `Tools`). Cross-reference each Grid-type parameter dict. Source: `turbopy/constructors.py` and the `input_data` docstring on `Simulation.__init__`.

### Pages to EDIT

- `docs/index.rst` — Extend the toctree to include, in order:
  ```
  getting_started
  overview
  simulation_lifecycle
  clock
  grids
  physics_modules
  compute_tools
  diagnostics
  dynamic_factory
  sharing_data
  input_files
  api
  ```
- `docs/api.rst` — (a) Fix typo `PhyiscsModule` → `PhysicsModule`. (b) Add `turbopy.constructors` autodoc section. (c) Consider adding `:inherited-members:` on the `automodule` calls so inherited methods from `DynamicFactory` show up on subclasses.
- `docs/getting_started.rst` — Expand: add a subsection "Your first turboPy app" that walks through defining a minimal `PhysicsModule`, registering it, and running a `Simulation` from a Python dict (do not require TOML). Add a "Running the test suite" subsection with the coverage invocation from `CLAUDE.md`.
- `docs/conf.py` — See section 4 below.

---

## 3. Audit of Docstrings in `turbopy/*.py`

Legend: **[MISSING]** = no docstring; **[THIN]** = one-line or missing `Parameters`/`Returns`/`Attributes` per numpydoc; **[FIX]** = present but incomplete or has a specific problem.

### `turbopy/core.py`

- `Simulation.__init__` — [THIN] no per-attribute Parameters section on `__init__` itself (relies on class docstring — this is fine per numpydoc convention; **no action needed**).
- `Simulation.combine_dictionaries` — [MISSING].
- `Simulation.parse_diagnostic_input_dictionary` — [MISSING] (has only inline comment).
- `Simulation.gather_shared_resources` — [MISSING]. Public method used by `PhysicsModule.exchange_resources`.
- `Simulation.find_tool_by_name` — [THIN] one-line; missing `Parameters`, `Returns`, note on returning `None` when 0 or >1 matches found.
- `Simulation.read_clock_from_input` — [THIN] one-liner. Add Notes describing what happens when `"Clock"` key is missing (`KeyError`).
- `Simulation.read_tools_from_input` — [THIN] one-liner. Should note the branching on `list` vs single dict and the `custom_name` behavior.
- `Simulation.read_modules_from_input` — [THIN] one-liner. Should note it also calls `sort_modules`.
- `Simulation.read_diagnostics_from_input` — [THIN]. Should describe (a) the split between diagnostics-by-name and default parameters (via `Diagnostic.is_valid_name`), (b) the default filename naming scheme (`{diag_type}{file_num}.{output_type}`), (c) default directory `"default_output"`.
- `Simulation.sort_modules` — [FIX] docstring says "Unused stub for future implementation"; retain, add `Notes` clarifying nothing depends on it.
- `Simulation.__repr__` — [MISSING].

- `DynamicFactory` — class docstring [THIN]. Add: usage example showing register/lookup, note on `override=False`.
- `DynamicFactory.register` — [THIN] add `Parameters`, `Raises` (`ValueError` if already registered without `override=True`, `TypeError` if not subclass), `Notes`.
- `DynamicFactory.lookup` — [THIN] add `Parameters`, `Returns`, `Raises` (`KeyError`).
- `DynamicFactory.is_valid_name` — [THIN] add `Parameters`, `Returns`.

- `PhysicsModule.publish_resource` — [FIX] convert prose "Deprecated" note to `.. deprecated:: <version>`.
- `PhysicsModule.inspect_resource` — [FIX] same.
- `PhysicsModule.inspect_resources` — [MISSING].
- `PhysicsModule.exchange_resources` — mention `Simulation.gather_shared_resources` and prepare_simulation.
- `PhysicsModule.update` — [THIN] mention subclasses MUST override; `NotImplementedError`.
- `PhysicsModule.__repr__` — [MISSING].

- `ComputeTool.initialize` — [THIN] add Notes about when it's called by `Simulation.prepare_simulation`.
- `ComputeTool.__repr__` — [MISSING].

- `SimulationClock.advance` — [THIN] describe side effects on `self.time`, `self.this_step`, conditional print via `print_time`.
- `SimulationClock.turn_back` — [THIN] add `Parameters` (`num_steps` default `1`), describe side effects.
- `SimulationClock.is_running` — [THIN] add `Returns` `bool`.
- `SimulationClock.__repr__` — [MISSING].

- `GridBase.__repr__` — [MISSING].
- `Grid.set_grid_points` — [MISSING].
- `Grid.generate_field` — list allowed `placement_of_points` explicitly; contrast with 2D grids.
- `Grid.set_volume_and_area_elements`, `set_cartesian_volumes`, `set_cylindrical_volumes`, `set_spherical_volumes`, `set_cartesian_areas`, `set_cylindrical_areas`, `set_spherical_areas`, `set_interface_volumes` — [MISSING] add at least one-line docstrings.

- `Diagnostic.inspect_resource` — [FIX] convert to `.. deprecated::`.
- `Diagnostic.inspect_resources` — [MISSING].
- `Diagnostic.__repr__` — [MISSING].

- Module-level helpers `wrap_item_in_list`, `make_values_into_lists` — [MISSING]. Add one-liners.

### `turbopy/computetools.py`

- `FiniteDifference.__init__` — [THIN] add `Raises TypeError` for non-1D grid.
- `BorisPush.push` — [FIX] add explicit note about in-place mutation of `position` and `momentum`.
- `Interpolators.interpolate1D` — mention allowed values for `kind` (passed to `scipy.interpolate.interp1d`).
- `FiniteDifference2D.__init__` — [THIN] mention `Raises TypeError` for a 1D grid.

### `turbopy/diagnostics.py`

- `OutputUtility.__init__` — [MISSING].
- `OutputUtility.diagnose`/`finalize`/`write_data` (abstract) — [THIN] expand each to describe contract for implementations.
- `PrintOutputUtility` — class docstring [THIN]. **[LATENT BUG]** does not implement abstract `finalize`/`write_data`. Flag; do not silently patch.
- `IntervalHandler.perform_action` — [THIN] add `Parameters` (`time`).
- `PointDiagnostic` — class docstring [THIN]: add one-line summary. **[FIX]** Attributes references `csv` — should be `outputter`, `interval`, `handler`. Same fix in `.initialize`.
- `FieldDiagnostic` — class docstring [THIN]: add one-line summary. `.diagnose` — [MISSING]. Fix `self.csv` → `self.outputter` in `.initialize`.
- `GridDiagnostic` — class docstring [THIN]: describe 2D vs 1D branch. **[FIX]** Attributes lists `owner`/`input_data` incorrectly. Fix typo "diagnotic" in comment.
- `GridDiagnostic.initialize` — [THIN] mention branch on grid type.
- `ClockDiagnostic` — class docstring **[FIX]** — Attributes lists `owner`/`input_data` which don't exist as public attributes.
- `HistoryDiagnostic` — add `Raises` section noting `NotImplementedError` on 2D grids.
- `HistoryDiagnostic.diagnose`, `.do_diagnostic`, `.initialize`, `.finalize` — [MISSING] all four.

### `turbopy/constructors.py`

- `construct_simulation_from_toml` — OK.
- Module docstring — [THIN] expand to describe the file format and cross-reference `Simulation`.

### `turbopy/__init__.py`

- Module docstring — [THIN]. Should list public re-exports so `help(turbopy)` is useful.

---

## 4. Sphinx `conf.py` Changes

File: `/Users/ndisner/github/turbopy/docs/conf.py`

- **napoleon** — already enabled with `napoleon_numpy_docstring = True`. No change.
- **autodoc** — enabled. Recommend adding:
  ```python
  autodoc_default_options = {
      'members': True,
      'inherited-members': True,
      'show-inheritance': True,
      'special-members': '__init__',
  }
  ```
- **autosummary** — not enabled. Recommend adding `'sphinx.ext.autosummary'` to `extensions` and `autosummary_generate = True`.
- **viewcode** — recommend adding `'sphinx.ext.viewcode'`.
- **`release`** — currently hard-coded to `'v2023.06.09'`. Should be pulled from `turbopy.__version__`.
- **`html_sidebars`** — references alabaster templates but theme is `sphinx_rtd_theme`; recommend removing.
- **`intersphinx_mapping`** — URLs use `http://`; upgrade to `https://` and canonical paths.
- **`master_doc`** — set twice; remove duplicate.

---

## 5. Files to Create or Edit

### Create (docs)
- `/Users/ndisner/github/turbopy/docs/overview.rst`
- `/Users/ndisner/github/turbopy/docs/simulation_lifecycle.rst`
- `/Users/ndisner/github/turbopy/docs/clock.rst`
- `/Users/ndisner/github/turbopy/docs/grids.rst`
- `/Users/ndisner/github/turbopy/docs/physics_modules.rst`
- `/Users/ndisner/github/turbopy/docs/compute_tools.rst`
- `/Users/ndisner/github/turbopy/docs/diagnostics.rst`
- `/Users/ndisner/github/turbopy/docs/dynamic_factory.rst`
- `/Users/ndisner/github/turbopy/docs/input_files.rst`

### Edit (docs)
- `/Users/ndisner/github/turbopy/docs/index.rst`
- `/Users/ndisner/github/turbopy/docs/api.rst`
- `/Users/ndisner/github/turbopy/docs/getting_started.rst`
- `/Users/ndisner/github/turbopy/docs/conf.py`

### Edit (code — docstrings only, no logic changes)
- `/Users/ndisner/github/turbopy/turbopy/core.py`
- `/Users/ndisner/github/turbopy/turbopy/computetools.py`
- `/Users/ndisner/github/turbopy/turbopy/diagnostics.py`
- `/Users/ndisner/github/turbopy/turbopy/constructors.py`
- `/Users/ndisner/github/turbopy/turbopy/__init__.py`

---

## 6. Acceptance Criteria

1. `cd /Users/ndisner/github/turbopy/docs && make html` completes with **zero new warnings** relative to `main`.
2. Every "Pages to CREATE" file exists and is reachable from `docs/index.rst` via the toctree; each renders headings and at least one `:class:` cross-reference into `turbopy.core`.
3. Every [MISSING]/[THIN] symbol in Section 3 has a numpydoc docstring with a one-line summary and appropriate `Parameters`/`Returns`/`Raises`/`Attributes` sections.
4. Every [FIX] symbol has the specific issue corrected (typos, wrong attribute names, `.. deprecated::`).
5. `pytest` still passes with no test changes.
6. `conf.py` changes from Section 4 are applied; `release` derives from `turbopy.__version__`.
7. Latent bugs (`PrintOutputUtility` missing abstract methods; `PointDiagnostic`/`FieldDiagnostic` docstrings referencing removed `self.csv`) are either fixed or flagged; do not silently alter runtime behavior.
