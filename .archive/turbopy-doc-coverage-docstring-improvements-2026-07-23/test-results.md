# Stage 3: Tester Results

## Pytest

- **Result: PASS**
- **105 passed**, 0 failed, 5 warnings (all pre-existing, unrelated to this PR):
  - 3 x `UserWarning: No Grid Found.` in `tests/test_bos.py` (BOS fixture doesn't include a Grid — expected).
  - 1 x `RuntimeWarning: invalid value encountered in divide` in `tests/test_computetools.py::test_poisson_solver` (division by `r=0` at the axis — pre-existing).
  - 1 x `DeprecationWarning: The resource-sharing API has changed.` from the intentional deprecation path.
- Command: `pytest --maxfail=5 -q` (executed from `/Users/ndisner/github/turbopy`).
- Runtime: ~0.39s.

## Sphinx build (baseline, `main` snapshot via `git stash`)

- **Exit code: 0**
- **Warning count: 10** (as reported by Sphinx's own `build succeeded, 10 warnings.` summary).
- Unique WARNING/ERROR/CRITICAL lines observed:
  - `turbopy.core.Diagnostic.inspect_resource:10` — ERROR: Unexpected indentation. [docutils]
  - `turbopy.core.Diagnostic.inspect_resource:11` — WARNING: Block quote ends without a blank line; unexpected unindent. [docutils]
  - `turbopy.core.Grid.generate_linear:5` — CRITICAL: Unexpected section title (`Returns` heading).
  - `turbopy.diagnostics.FieldDiagnostic.diagnose:1` — WARNING: duplicate object description in `api` (autodoc double-registered).
  - 6 x `WARNING: unsupported theme option '...' given` (`github_user`, `github_repo`, `description`, `github_banner`, `github_button`, `travis_button`) — leftover alabaster theme options in `conf.py` under `sphinx_rtd_theme`.
- Log: `/tmp/turbopy-sphinx-baseline.log`.

## Sphinx build (after changes)

- **Exit code: 0**
- **Warning count: 7** (Sphinx summary: `build succeeded, 7 warnings.`).
- Unique WARNING/ERROR/CRITICAL lines observed:
  - `turbopy.core.Grid.generate_linear:5` — CRITICAL: Unexpected section title (`Returns` heading). *(Pre-existing; `Grid.generate_linear` was not in scope for this PR.)*
  - 6 x `WARNING: unsupported theme option '...' given` (same 6 as baseline).
- Log: `/tmp/turbopy-sphinx-after.log`.

## New warnings introduced

**None.** No warning or error line present in the "after" log is absent from the baseline log.

## Warnings resolved

Three warnings that were present on `main` are gone after this PR:

1. `turbopy.core.Diagnostic.inspect_resource:10` — ERROR: Unexpected indentation. [docutils]
2. `turbopy.core.Diagnostic.inspect_resource:11` — WARNING: Block quote ends without a blank line; unexpected unindent. [docutils]
3. `turbopy.diagnostics.FieldDiagnostic.diagnose:1` — WARNING: duplicate object description of `turbopy.diagnostics.FieldDiagnostic.diagnose`.

Warnings 1–2 are resolved because the coder converted the prose "Deprecated" note on `Diagnostic.inspect_resource` to a `.. deprecated::` directive (per Section 3 of the spec). Warning 3 is resolved as a side effect of adding a proper docstring to `FieldDiagnostic.diagnose` (previously `[MISSING]`).

## Verdict

**PASS** — pytest is green (105/105) and the Sphinx warning count decreased from 10 to 7 with zero new warnings, satisfying Acceptance Criterion 1 (`zero new warnings relative to main`) and Acceptance Criterion 5 (`pytest still passes`).

## Notes

- The 6 `unsupported theme option` warnings and the `Grid.generate_linear` CRITICAL are pre-existing and untouched by this PR. `Grid.generate_linear` was not listed in the spec's Section 3 audit. The theme-option warnings originate from a stray alabaster-era block in `docs/conf.py` that the coder chose not to prune (the spec called out `html_sidebars` removal explicitly, but not these `html_theme_options` keys); consider a follow-up.
- Sphinx `autosummary` was newly enabled by the PR; the "after" build includes an `[autosummary] generating autosummary for: ...` step that lists all 13 source files. No autosummary-generation warnings were produced.
- The `git stash push -u` / `git stash pop` cycle worked cleanly (a stash was created and popped without conflict). Both builds were performed against a clean `_build` directory via `make clean`.
- Only file paths cited above are `/tmp/turbopy-sphinx-baseline.log` and `/tmp/turbopy-sphinx-after.log`, which remain on disk for follow-up inspection if desired.
