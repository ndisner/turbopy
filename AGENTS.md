# turboPy — Agent Instructions

Project overview, dev setup, testing commands, architecture, and coding conventions live in [`CLAUDE.md`](CLAUDE.md) — read that first. This file only covers the repo-local agents, skills, and prompts and when to invoke them.

## Agents (`.claude/agents/`)

| Agent | Use when |
|-------|----------|
| `planner` | Starting multi-file / cross-module work. Produces a phased plan (Grid/ComputeTool → PhysicsModule → Diagnostic → Integration). |
| `code-architect` | Making a design decision that affects the class hierarchy, dispatch, or shared-resource contract. |
| `code-explorer` | Read-only discovery — "where is X defined", "what consumes resource Y". Use before editing unfamiliar areas. |
| `python-reviewer` | Reviewing modified `.py` files for turboPy patterns (registry, `_needed_resources`, grid dispatch, numerical assertions). |
| `tdd-guide` | Adding a new `PhysicsModule` / `ComputeTool` / `Diagnostic` / `Grid` variant, or fixing a bug. Enforces `pytest` RED → GREEN → REFACTOR. |

## Skills (`.claude/skills/`)

| Skill | Use when |
|-------|----------|
| `tdd-workflow` | Driving a full pytest TDD loop with turboPy-specific fixture and dispatch patterns. |
| `python-patterns` | Writing idiomatic Python contributions (immutability, typing, small focused modules). |
| `python-testing` | Choosing fixtures, structuring `tests/test_*.py`, writing numerical assertions with correct tolerances. |

## Prompts (`.github/prompts/`)

| Prompt | Use when |
|--------|----------|
| `plan` | Producing a phased implementation plan before code. |
| `tdd` | Kicking off a single RED → GREEN → REFACTOR cycle. |
| `build-fix` | Diagnosing a `pytest` failure, import error, or packaging issue. |
| `refactor` | Cleaning up dead code / duplication without changing behavior. |
| `security-review` | Reviewing input-handling or file/path operations for injection or path-traversal risks. |

## When to Invoke What

- **New feature or bug fix** → `planner` (if multi-file) → `tdd-guide` → `python-reviewer`.
- **Unfamiliar code** → `code-explorer` before editing.
- **Design choice affecting dispatch or shared resources** → `code-architect`.
- **Build / test failing** → `build-fix` prompt.
- **Post-implementation cleanup** → `refactor` prompt (keep tests green).

Multiple independent agents can run in parallel — e.g. `code-explorer` and `python-reviewer` on different files at once.

## Notes

- These agents assume the pytest / conda / `pip install -e .` workflow in `CLAUDE.md`.
- turboPy is a scientific Python library — ignore any generic agent guidance about web-app concerns (SQL/XSS/CSRF, npm/Jest/Playwright, secret rotation). If a copied-in agent still references those, prune it.
