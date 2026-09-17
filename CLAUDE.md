@AGENTS.md

# Claude Code delta

`AGENTS.md` is intentionally imported as the shared stable implementation policy in this bootstrap repository.

- Claude-specific project configuration lives under `.claude/`.
- Confirm effective project settings with current Claude Code diagnostics/status when materializing or changing harness configuration.
- Do not treat Claude auto-memory as project authority; GitHub, tracked repository state, Issues, and the active task contract remain authoritative according to `AGENTS.md`.
- During downstream materialization, a Claude-only project may move the required stable rules into `CLAUDE.md` and remove `AGENTS.md`; a dual-harness project should normally keep the import to avoid duplicated stable rules.
