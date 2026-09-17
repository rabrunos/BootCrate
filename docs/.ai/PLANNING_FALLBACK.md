# Planning Fallback — materialization skeleton

Primary project orchestration uses ChatGPT.

Codex Plan Mode or Claude Code Plan Mode is a fallback when ChatGPT is unavailable, limited, or intentionally bypassed.

A fallback planner should:

1. inspect local branch/HEAD/status/diff;
2. read the applicable stable harness instructions;
3. use `CONTEXT_INDEX.md` to load only relevant project context;
4. inspect relevant GitHub Issues when the task depends on tracked state and access is available;
5. preserve owner decisions and Issue authority;
6. apply `TASK_POLICY.md`;
7. resolve scope/acceptance before implementation begins;
8. avoid creating checkpoint/status/decision-index files to preserve planning state — use Git and Issues.

Fallback planning must not silently weaken safety/publication restrictions or turn unresolved product decisions into implementation assumptions.
