Run the full turboPy feature pipeline for: $ARGUMENTS

You are orchestrating four subagents through a strict, status-driven pipeline. Do not skip stages. After each stage, read the `STATUS:` line at the top of its handoff file and use the routing table below. Do not paraphrase the agents' work — surface their handoff files verbatim when stopping.

## Pre-flight

1. If `.pipeline/spec.md` already exists, archive the current `.pipeline/` contents:
   - Read the first line of `.pipeline/spec.md` to get the previous feature title.
   - Move all files under `.pipeline/` into a new folder `.archive/<slug-of-title>-<YYYY-MM-DD>/`.
   - Recreate an empty `.pipeline/` directory.
2. Confirm the working tree state with `git status --short` and note it — a dirty tree at pipeline start becomes ambiguous later.

## The four stages

Run each stage in order. Wait for the named handoff file to exist before moving on.

| # | Agent | Handoff file | Tools it needs (verify before invoking) |
|---|---|---|---|
| 1 | `planner` | `.pipeline/spec.md` | Read, Grep, Glob, Write |
| 2 | `coder` | `.pipeline/changes.md` | Read, Grep, Glob, Edit, Write, Bash |
| 3 | `tester` | `.pipeline/test-results.md` | Read, Grep, Glob, Edit, Write, Bash |
| 4 | `reviewer` | `.pipeline/review.md` | Read, Grep, Glob, Bash, Write |

### Toolset fallback

If a subagent lacks the tools it needs to complete its stage (e.g., it returns its handoff as text rather than writing the file), do NOT retry the same subagent. Route the stage through the `general-purpose` subagent instead, and pass along the full contents of the corresponding `.claude/agents/<stage>.md` playbook as its prompt so the general-purpose agent applies the same rules. This is the belt-and-suspenders path for permissions or tool-manifest problems.

## Status routing

After every stage, read the `STATUS:` line at the top of the handoff file. Route based on it:

| STATUS | Action |
|---|---|
| `READY` | Advance to the next stage. |
| `BLOCKED` | Stop the pipeline. Show the user the full handoff file. The user must resolve the block (typically by answering open questions in `spec.md`) before you re-run. Do not attempt to answer for them. |
| `FAILED` | Stop the pipeline. Show the user the full handoff file. Do not attempt to fix the failure yourself — the user decides whether to spin off a fix, revise the spec, or abandon. |
| (missing) | Treat as `FAILED`. The subagent did not produce a valid handoff. Show the user what the subagent returned and stop. |

## Final report

If all four stages return `STATUS: READY`, show the user:
1. The verdict from `.pipeline/review.md` (`## Recommendation` line).
2. A short summary of what was touched (count of files changed, count of tests added, pytest pass count).
3. The branch name and a reminder that nothing was pushed.

Do NOT merge, push, or open a PR. The user reviews in the morning.

## What the pipeline is not for

- One-line typo fixes — just edit the file.
- Pure research / codebase questions — use `code-explorer` or a direct search.
- Anything the user has already given detailed step-by-step instructions for — the pipeline exists to add structure to under-specified requests, not to gate work the user has already planned.

If the request is trivial, tell the user "this is trivial, skipping the pipeline" and just do it.
