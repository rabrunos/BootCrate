# File Lifecycle

## Bootstrap-only — remove after successful downstream materialization

- `docs/.human/bootstrap/**`
- raw `project-intake.json`
- generic library role/skill definitions
- BootCrate README/history/branding

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

## Generated tracked artifacts — project-specific

Examples, only when useful:

- source/build/project manifests;
- canonical version source;
- CI/workflows;
- build/test/run/package/install/diagnostics/publish scripts;
- source architecture map;
- validation/tooling map;
- external-target/native/runtime map;
- API/command/data/save/release maps;
- tests and fixtures;
- packaging/install configuration;
- specialized agents/skills.

## Local-only / generated evidence

Use ignored `.local/` for binaries, decompiled/extracted trees, symbol indexes, raw/sanitized logs, research tools, caches, build artifacts, screenshots/video, and temporary diagnostics.

Promote only compact stable conclusions into tracked project knowledge.

## Permanent stable in a materialized project

Only final project invariants such as harness instructions, versioning rules, safety/publication boundaries, and stable workflow rules.

## Permanent mutable

Source/config/tests, version source, context routing, project profile when stable facts/toolchain change, prompt templates when workflow changes, and GitHub Issues for active work/status.

## Pruning rule

Materialization is incomplete until irrelevant BootCrate files/adapters are deleted and tracked files contain no unintended bootstrap references.
