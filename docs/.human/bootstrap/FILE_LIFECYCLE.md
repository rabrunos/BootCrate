# File Lifecycle

## Bootstrap-only — remove after successful downstream materialization

- `docs/.human/bootstrap/**`
- raw `project-intake.json`
- generic library role/skill definitions
- this BootCrate README/history/branding

## Skeleton — adapt, keep only if the materialized project uses it

- `AGENTS.md`
- `CLAUDE.md`
- `.codex/**`
- `.agents/skills/**`
- `.claude/**`
- `docs/.ai/orchestration.md`
- `docs/.ai/TASK_POLICY.md`
- `docs/.ai/PLANNING_FALLBACK.md`
- `docs/.ai/CONTEXT_INDEX.md`
- `docs/.ai/LOCAL_WORKSPACE.md`
- `docs/.ai/project-profile.json`
- `docs/.ai/schemas/project-profile.schema.json`
- `docs/.ai/prompts/**`
- `.github/ISSUE_TEMPLATE/**`
- `.github/labels.yml`
- `scripts/README.md`

## Permanent stable in a materialized project

Only final project invariants such as harness instructions, safety/publication boundaries, and project workflow rules. These change rarely.

## Permanent mutable

Source/config/tests, context routing, project profile when stable facts/toolchain change, prompt templates when project workflow changes, and GitHub Issues for active work/status.

## Generated/project-specific

Build/run/test scripts, CI, packaging, diagnostics reducers, architecture maps, release tooling, integration configuration, and additional skills/agents only when the actual project requires them.

## Pruning rule

Materialization is incomplete until irrelevant BootCrate files/adapters are deleted and tracked files contain no unintended bootstrap references.
